package com.dreamwall;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.logging.Level;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.Lectern;
import org.bukkit.block.Sign;
import org.bukkit.block.data.type.Switch;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Display.Billboard;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.BookMeta;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

public final class DreamWallPlugin extends JavaPlugin implements Listener {
    private HttpClient httpClient;
    private BukkitTask pollTask;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(8))
                .build();
        getServer().getPluginManager().registerEvents(this, this);

        if (getConfig().getBoolean("poll-enabled", false)) {
            startPolling();
        }

        getLogger().info("DreamWall bridge enabled. Space: " + spaceUrl());
    }

    @Override
    public void onDisable() {
        if (pollTask != null) {
            pollTask.cancel();
        }
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length > 0 && args[0].equalsIgnoreCase("fetch")) {
            fetchSpace(sender);
            return true;
        }
        if (args.length > 0 && args[0].equalsIgnoreCase("demo")) {
            placeDemoArtifact(sender);
            return true;
        }
        if (args.length > 0 && args[0].equalsIgnoreCase("import")) {
            boolean placeHere = args.length > 1 && args[1].equalsIgnoreCase("here");
            importArtifact(sender, placeHere);
            return true;
        }
        if (args.length > 0 && args[0].equalsIgnoreCase("museum")) {
            handleMuseumCommand(sender, args);
            return true;
        }
        if (args.length > 0 && args[0].equalsIgnoreCase("pack")) {
            offerResourcePack(sender);
            return true;
        }

        sender.sendMessage("DreamWall bridge is configured for: " + spaceUrl());
        sender.sendMessage("Canvas: " + getConfig().getInt("canvas-size", 12) + "x" + getConfig().getInt("canvas-size", 12)
                + " plots, plot size=" + getConfig().getInt("plot-size", 32));
        sender.sendMessage("Use /dreamwall fetch to test Hugging Face reachability.");
        sender.sendMessage("Use /dreamwall pack to load the AfterBlockMuseum resource pack.");
        sender.sendMessage("Use /dreamwall demo in-game to place a safe AfterBlock pedestal and passport proof.");
        sender.sendMessage("Use /dreamwall import or /dreamwall import here to place a live Space artifact packet.");
        sender.sendMessage("Use /dreamwall museum where to inspect the exact plot map.");
        sender.sendMessage("Use /dreamwall museum build to create the 12x12 living museum campus.");
        return true;
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        if (getConfig().getBoolean("offer-resource-pack-on-join", false)) {
            getServer().getScheduler().runTaskLater(this, () -> sendResourcePack(event.getPlayer()), 40L);
        }
    }

    @EventHandler
    public void onPlayerInteract(PlayerInteractEvent event) {
        if (event.getAction() != Action.RIGHT_CLICK_BLOCK || event.getClickedBlock() == null) {
            return;
        }
        Block block = event.getClickedBlock();
        if (block.getType() != Material.WARPED_BUTTON) {
            return;
        }
        String key = spiritButtonKey(block.getLocation());
        if (!getConfig().contains(key + ".title")) {
            return;
        }
        event.setCancelled(true);
        Player player = event.getPlayer();
        String title = getConfig().getString(key + ".title", "AfterBlock Relic");
        String owner = getConfig().getString(key + ".owner", "@unknown");
        String hall = getConfig().getString(key + ".hall", "Museum");
        String memory = getConfig().getString(key + ".memory", "This relic has no written history yet.");
        String spirit = getConfig().getString(key + ".spirit", "I am what remained when a memory became a place.");
        String xyz = getConfig().getString(key + ".xyz", "unknown");

        player.sendTitle(compactItemName(title), compactLore(spirit), 5, 70, 15);
        player.sendMessage("AfterBlock spirit: " + compactLore(spirit));
        player.sendMessage("History: " + compactLore(memory));
        player.sendMessage("Hall: " + hall + " | Owner: " + owner + " | XYZ " + xyz);
    }

    private void startPolling() {
        long ticks = Math.max(20L, getConfig().getLong("poll-seconds", 30L) * 20L);
        pollTask = getServer().getScheduler().runTaskTimerAsynchronously(this, () -> {
            try {
                String body = get(spaceUrl() + "/config");
                getLogger().info("DreamWall poll ok, config bytes=" + body.length());
            } catch (IOException | InterruptedException e) {
                getLogger().log(Level.WARNING, "DreamWall poll failed", e);
                Thread.currentThread().interrupt();
            }
        }, ticks, ticks);
    }

    private void fetchSpace(CommandSender sender) {
        getServer().getScheduler().runTaskAsynchronously(this, () -> {
            try {
                String body = get(spaceUrl() + "/config");
                sender.sendMessage("DreamWall Space reachable. Config bytes=" + body.length());
                sender.sendMessage("Next step: call /gradio_api/call/quick_curate and import dreamwall.museum.v1.");
                sender.sendMessage("Use /dreamwall demo for a local pedestal proof with custom model data.");
                sender.sendMessage("Use /dreamwall pack to load the custom item models from Hugging Face.");
            } catch (IOException | InterruptedException e) {
                sender.sendMessage("DreamWall fetch failed: " + e.getMessage());
                Thread.currentThread().interrupt();
            }
        });
    }

    private void offerResourcePack(CommandSender sender) {
        sender.sendMessage("AfterBlockMuseum resource pack URL: " + resourcePackUrl());
        sender.sendMessage("SHA1: " + resourcePackSha1());
        if (sender instanceof Player player) {
            sendResourcePack(player);
        } else {
            sender.sendMessage("Run /dreamwall pack in-game to request the pack on a player client.");
        }
    }

    private void sendResourcePack(Player player) {
        String url = resourcePackUrl();
        if (url.isBlank()) {
            player.sendMessage("DreamWall resource-pack-url is blank in config.yml.");
            return;
        }
        byte[] sha1 = resourcePackSha1Bytes();
        if (sha1.length == 20) {
            player.setResourcePack(url, sha1);
        } else {
            player.setResourcePack(url);
        }
        player.sendMessage("Requested AfterBlockMuseum resource pack. Accept it to see CustomModelData relics.");
        player.sendMessage("Pack SHA1: " + resourcePackSha1());
    }

    private void importArtifact(CommandSender sender, boolean placeHere) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage("/dreamwall import must be run by an in-game player.");
            return;
        }
        sender.sendMessage("Importing one live AfterBlock artifact from " + spaceUrl() + " ...");
        getServer().getScheduler().runTaskAsynchronously(this, () -> {
            try {
                JsonObject packet = fetchMuseumPacket();
                getServer().getScheduler().runTask(this, () -> placePacketArtifact(player, packet, placeHere));
            } catch (IOException | InterruptedException e) {
                sender.sendMessage("DreamWall import failed: " + e.getMessage());
                Thread.currentThread().interrupt();
            } catch (RuntimeException e) {
                sender.sendMessage("DreamWall import parse failed: " + e.getMessage());
            }
        });
    }

    private JsonObject fetchMuseumPacket() throws IOException, InterruptedException {
        String payload = "{\"data\":[\"a white AirPods case from a first year desk\",\"A small object that carried private worlds through public noise.\",\"@afterblock\",null]}";
        String callBody = post(spaceUrl() + "/gradio_api/call/quick_curate", payload);
        JsonObject call = JsonParser.parseString(callBody).getAsJsonObject();
        String eventId = call.get("event_id").getAsString();
        String stream = get(spaceUrl() + "/gradio_api/call/quick_curate/" + eventId);
        for (String line : stream.split("\\R")) {
            if (line.startsWith("data: ")) {
                JsonArray outputs = JsonParser.parseString(line.substring(6)).getAsJsonArray();
                for (JsonElement output : outputs) {
                    if (!output.isJsonPrimitive() || !output.getAsJsonPrimitive().isString()) {
                        continue;
                    }
                    String candidate = output.getAsString();
                    if (!candidate.contains("\"dreamwall.museum.v1\"")) {
                        continue;
                    }
                    JsonObject packet = JsonParser.parseString(candidate).getAsJsonObject();
                    String type = text(packet, "type", "");
                    if ("dreamwall.museum.v1".equals(type)) {
                        return packet;
                    }
                }
                throw new IOException("dreamwall.museum.v1 packet was not present in Gradio outputs");
            }
        }
        throw new IOException("no data event returned by Gradio");
    }

    private void placePacketArtifact(Player player, JsonObject packet, boolean placeHere) {
        JsonObject minecraft = packet.getAsJsonObject("minecraft");
        JsonObject artifact = packet.getAsJsonObject("artifact");
        JsonObject coordinates = minecraft.getAsJsonObject("coordinates");
        World world = player.getWorld();
        Location base = placeHere
                ? player.getLocation().getBlock().getLocation().add(0, 0, 2)
                : new Location(world, number(coordinates, "x", player.getLocation().getBlockX()),
                        number(coordinates, "y", player.getLocation().getBlockY()),
                        number(coordinates, "z", player.getLocation().getBlockZ()));
        world.getChunkAt(base).load(true);

        Material pedestalMaterial = materialFromPacket(minecraft);
        base.getBlock().setType(pedestalMaterial);
        base.clone().add(0, 1, 0).getBlock().setType(Material.AMETHYST_BLOCK);

        Block signBlock = base.clone().add(0, 1, -1).getBlock();
        signBlock.setType(Material.OAK_SIGN);
        String title = text(minecraft, "title", text(artifact, "title", "AfterBlock Relic"));
        String owner = text(minecraft, "owner_handle", text(artifact, "owner_handle", "@unknown"));
        String hall = text(minecraft, "hall", text(artifact, "hall", "Museum"));
        String plaque = text(minecraft, "plaque_text", text(artifact, "plaque_line", "Preserved in AfterBlock"));
        String zone = text(artifact, "zone", "Museum route");
        String memory = text(artifact, "memory_text", plaque);
        String spirit = text(minecraft, "spirit_first_line", text(artifact, "spirit_first_line", plaque));
        if (signBlock.getState() instanceof Sign sign) {
            sign.setLine(0, trimLine(title));
            sign.setLine(1, trimLine(owner));
            sign.setLine(2, trimLine(hall));
            sign.setLine(3, trimLine(plaque));
            sign.update();
        }

        int customModelData = integer(minecraft, "custom_model_data", 730001);
        String command = giveCommand(customModelData);
        ItemStack item = artifactItem(title, customModelData,
                List.of("Owner: " + owner, "Hall: " + hall, "XYZ: " + base.getBlockX() + " " + base.getBlockY() + " " + base.getBlockZ(), compactLore(memory)));
        ItemStack passport = passportBook(title, owner, hall, zone, memory, spirit, command, base, customModelData);
        player.getInventory().addItem(item, passport);
        placeDisplayRelic(world, base, item);
        placePassportLectern(world, base, passport);
        placeSpiritButton(world, base, title, owner, hall, memory, spirit);
        if (!placeHere) {
            placeLivingRoute(world, base, title, owner, hall);
            player.setCompassTarget(base);
            player.getInventory().addItem(routeCompass(title, owner, hall, base));
            player.sendTitle("YOU ARE HERE", "Follow lights to " + compactItemName(title), 10, 70, 20);
        }
        world.spawnParticle(Particle.ENCHANT, base.clone().add(0.5, 1.4, 0.5), 38, 0.45, 0.65, 0.45, 0.015);
        player.sendMessage("Imported " + title + " by " + owner + " into " + hall + ".");
        player.sendMessage("Displayed item, placed passport lectern, and gave CustomModelData " + customModelData + ".");
        if (!placeHere) {
            player.sendMessage("Placed at packet coordinates " + base.getBlockX() + " " + base.getBlockY() + " " + base.getBlockZ()
                    + " and updated the lit route from YOU ARE HERE.");
            player.sendMessage("Your compass now points to the relic plot.");
            player.sendMessage("Use /dreamwall import here for a nearby proof.");
        }
    }

    private void placeDemoArtifact(CommandSender sender) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage("/dreamwall demo must be run by an in-game player.");
            return;
        }
        Location base = player.getLocation().getBlock().getLocation().add(0, 0, 2);
        World world = base.getWorld();
        if (world == null) {
            sender.sendMessage("Could not find world.");
            return;
        }

        Block pedestal = base.getBlock();
        pedestal.setType(Material.POLISHED_DEEPSLATE);
        base.clone().add(0, 1, 0).getBlock().setType(Material.AMETHYST_BLOCK);

        Block signBlock = base.clone().add(0, 1, -1).getBlock();
        signBlock.setType(Material.OAK_SIGN);
        if (signBlock.getState() instanceof Sign sign) {
            sign.setLine(0, "AfterBlock");
            sign.setLine(1, "AirPods Relic");
            sign.setLine(2, "@Wildstash");
            sign.setLine(3, "Private worlds");
            sign.update();
        }

        ItemStack item = artifactItem("AfterBlock AirPods Relic", 730002,
                List.of("Owner: @Wildstash", "Hall: Hall of Companions", "XYZ: " + base.getBlockX() + " " + base.getBlockY() + " " + base.getBlockZ(), "Private worlds through public noise."));
        ItemStack passport = passportBook(
                "AfterBlock AirPods Relic",
                "@Wildstash",
                "Hall of Companions",
                "Quiet Bench Passage",
                "A small object that carried private worlds through public noise.",
                "I am what remained when a pocket object became a place.",
                giveCommand(730002),
                base,
                730002);
        player.getInventory().addItem(item, passport);
        placeDisplayRelic(world, base, item);
        placePassportLectern(world, base, passport);
        placeSpiritButton(world, base, "AfterBlock AirPods Relic", "@Wildstash", "Hall of Companions",
                "A small object that carried private worlds through public noise.",
                "I am what remained when a pocket object became a place.");
        world.spawnParticle(Particle.ENCHANT, base.clone().add(0.5, 1.4, 0.5), 28, 0.35, 0.55, 0.35, 0.01);
        sender.sendMessage("Placed demo pedestal, displayed relic item, lectern passport, spirit button, and gave Paper item with CustomModelData 730002.");
        sender.sendMessage("Run /dreamwall pack and accept the pack to see the generated item model.");
    }

    private void handleMuseumCommand(CommandSender sender, String[] args) {
        if (args.length < 2 || args[1].equalsIgnoreCase("where")) {
            sendMuseumMap(sender);
            return;
        }
        if (args[1].equalsIgnoreCase("build")) {
            buildMuseumCampus(sender);
            return;
        }
        if (args[1].equalsIgnoreCase("check")) {
            checkMuseumCampus(sender);
            return;
        }
        sender.sendMessage("Use /dreamwall museum where, /dreamwall museum build, or /dreamwall museum check.");
    }

    private void sendMuseumMap(CommandSender sender) {
        int originX = galleryOriginX();
        int originY = galleryOriginY();
        int originZ = galleryOriginZ();
        int canvasSize = canvasSize();
        int plotSize = plotSize();
        int lastX = originX + (canvasSize - 1) * plotSize;
        int lastZ = originZ + (canvasSize - 1) * plotSize;
        sender.sendMessage("AfterBlock museum coordinate map:");
        sender.sendMessage("Plot (0,0) -> XYZ " + originX + " " + originY + " " + originZ);
        sender.sendMessage("Plot (" + (canvasSize - 1) + "," + (canvasSize - 1) + ") -> XYZ " + lastX + " " + originY + " " + lastZ);
        sender.sendMessage("Formula: x=" + originX + " + plotX*" + plotSize + ", z=" + originZ + " + plotZ*" + plotSize + ".");
        sender.sendMessage("Run /dreamwall museum build to create pads, hall gates, banners, and a You Are Here entry.");
        sender.sendMessage("Then run /dreamwall import to place a Space artifact at its packet coordinates.");
    }

    private void buildMuseumCampus(CommandSender sender) {
        World world = museumWorld(sender);
        if (world == null) {
            sender.sendMessage("DreamWall gallery-world is not loaded: " + getConfig().getString("gallery-world", "world"));
            return;
        }
        int originX = galleryOriginX();
        int originY = galleryOriginY();
        int originZ = galleryOriginZ();
        int canvasSize = canvasSize();
        int plotSize = plotSize();
        int span = (canvasSize - 1) * plotSize;

        sender.sendMessage("Building AfterBlock Museum campus at plot (0,0) XYZ "
                + originX + " " + originY + " " + originZ + " ...");

        buildMemoryRails(world, originX, originY, originZ, canvasSize, plotSize, span);
        buildPlotPads(world, originX, originY, originZ, canvasSize, plotSize);
        buildHallGates(world, originX, originY, originZ, plotSize);
        buildEntrance(world, originX, originY, originZ, canvasSize, plotSize, span);
        world.save();

        if (sender instanceof Player player && player.getWorld().equals(world)) {
            player.teleport(new Location(world, originX + span / 2.0 + 0.5, originY + 2, originZ - 22.5, 0, 0));
        }
        sender.sendMessage("AfterBlock Museum campus built. Every Space packet coordinate now lands on a marked plot pad.");
        sender.sendMessage("Built " + (canvasSize * canvasSize) + " plot pads, 9 hall gates, and 1 YOU ARE HERE entry beacon.");
        sender.sendMessage("Next: /dreamwall pack, accept the pack, then /dreamwall import or /dreamwall import here.");
    }

    private void checkMuseumCampus(CommandSender sender) {
        World world = museumWorld(sender);
        if (world == null) {
            sender.sendMessage("DreamWall gallery-world is not loaded: " + getConfig().getString("gallery-world", "world"));
            return;
        }
        int originX = galleryOriginX();
        int originY = galleryOriginY();
        int originZ = galleryOriginZ();
        int canvasSize = canvasSize();
        int plotSize = plotSize();
        int span = (canvasSize - 1) * plotSize;
        int pads = 0;
        int relicBlocks = 0;
        for (int plotX = 0; plotX < canvasSize; plotX++) {
            for (int plotZ = 0; plotZ < canvasSize; plotZ++) {
                int x = originX + plotX * plotSize;
                int z = originZ + plotZ * plotSize;
                if (world.getBlockAt(x, originY, z).getType() == Material.POLISHED_DEEPSLATE) {
                    pads++;
                }
                if (world.getBlockAt(x, originY + 1, z).getType() == Material.AMETHYST_BLOCK) {
                    relicBlocks++;
                }
            }
        }
        int centerX = originX + span / 2;
        int entryZ = originZ - 22;
        boolean entryBeacon = world.getBlockAt(centerX, originY + 1, entryZ + 2).getType() == Material.BEACON;
        sender.sendMessage("AfterBlock museum check:");
        sender.sendMessage("Plot pads: " + pads + "/" + (canvasSize * canvasSize));
        sender.sendMessage("Relic focus blocks: " + relicBlocks + "/" + (canvasSize * canvasSize));
        sender.sendMessage("YOU ARE HERE beacon: " + (entryBeacon ? "present" : "missing"));
        sender.sendMessage("Expected bounds: -192 80 -192 to 160 80 160 unless config overrides gallery-origin or plot-size.");
    }

    private World museumWorld(CommandSender sender) {
        if (sender instanceof Player player) {
            return player.getWorld();
        }
        return getServer().getWorld(getConfig().getString("gallery-world", "world"));
    }

    private void buildMemoryRails(World world, int originX, int y, int originZ, int canvasSize, int plotSize, int span) {
        int minX = originX - 8;
        int maxX = originX + span + 8;
        int minZ = originZ - 8;
        int maxZ = originZ + span + 8;
        for (int plot = 0; plot < canvasSize; plot++) {
            int lineX = originX + plot * plotSize;
            int lineZ = originZ + plot * plotSize;
            for (int z = minZ; z <= maxZ; z++) {
                setBlock(world, lineX - 1, y - 1, z, Material.POLISHED_BLACKSTONE);
                setBlock(world, lineX, y - 1, z, Material.DEEPSLATE_TILES);
                setBlock(world, lineX + 1, y - 1, z, Material.POLISHED_BLACKSTONE);
            }
            for (int x = minX; x <= maxX; x++) {
                setBlock(world, x, y - 1, lineZ - 1, Material.POLISHED_BLACKSTONE);
                setBlock(world, x, y - 1, lineZ, Material.DEEPSLATE_TILES);
                setBlock(world, x, y - 1, lineZ + 1, Material.POLISHED_BLACKSTONE);
            }
        }
        for (int x = minX; x <= maxX; x++) {
            setBlock(world, x, y - 1, minZ, Material.CHISELED_POLISHED_BLACKSTONE);
            setBlock(world, x, y - 1, maxZ, Material.CHISELED_POLISHED_BLACKSTONE);
        }
        for (int z = minZ; z <= maxZ; z++) {
            setBlock(world, minX, y - 1, z, Material.CHISELED_POLISHED_BLACKSTONE);
            setBlock(world, maxX, y - 1, z, Material.CHISELED_POLISHED_BLACKSTONE);
        }
    }

    private void buildPlotPads(World world, int originX, int y, int originZ, int canvasSize, int plotSize) {
        for (int plotX = 0; plotX < canvasSize; plotX++) {
            for (int plotZ = 0; plotZ < canvasSize; plotZ++) {
                int x = originX + plotX * plotSize;
                int z = originZ + plotZ * plotSize;
                int hall = hallIndexForPlot(plotX, plotZ);
                Material accent = hallAccent(hall);
                for (int dx = -5; dx <= 5; dx++) {
                    for (int dz = -5; dz <= 5; dz++) {
                        boolean edge = Math.abs(dx) == 5 || Math.abs(dz) == 5;
                        setBlock(world, x + dx, y - 1, z + dz, edge ? accent : Material.SMOOTH_BASALT);
                    }
                }
                setBlock(world, x, y, z, Material.POLISHED_DEEPSLATE);
                setBlock(world, x, y + 1, z, Material.AMETHYST_BLOCK);
                setBlock(world, x - 4, y, z - 4, Material.SEA_LANTERN);
                setBlock(world, x + 4, y, z - 4, Material.SEA_LANTERN);
                setBlock(world, x - 4, y, z + 4, Material.SEA_LANTERN);
                setBlock(world, x + 4, y, z + 4, Material.SEA_LANTERN);
                placePlotSign(world, x, y, z, plotX, plotZ);
            }
        }
    }

    private void buildHallGates(World world, int originX, int y, int originZ, int plotSize) {
        String[] names = {
                "Hall of Firsts", "Hall of Companions", "Turning Points",
                "Hall of Worlds", "Soft Things", "Hall of Tools",
                "Lost Signals", "Painting Hall", "Spirit Grove"
        };
        String[] subtitles = {
                "Threshold Arcade", "Quiet Bench Passage", "Pressure Door",
                "Blue Lantern Corridor", "Shelter Nook", "Workshop Walk",
                "Static Archive", "Frame Gallery", "Living Atrium"
        };
        for (int hall = 0; hall < names.length; hall++) {
            int regionX = hall % 3;
            int regionZ = hall / 3;
            int centerX = originX + regionX * plotSize * 4 + plotSize + plotSize / 2;
            int centerZ = originZ + regionZ * plotSize * 4 + plotSize + plotSize / 2;
            Material accent = hallAccent(hall);
            for (int dx = -7; dx <= 7; dx++) {
                setBlock(world, centerX + dx, y, centerZ, accent);
                setBlock(world, centerX + dx, y + 5, centerZ, accent);
            }
            for (int dy = 1; dy <= 4; dy++) {
                setBlock(world, centerX - 7, y + dy, centerZ, Material.DARK_OAK_LOG);
                setBlock(world, centerX + 7, y + dy, centerZ, Material.DARK_OAK_LOG);
            }
            setBlock(world, centerX - 9, y + 2, centerZ, bannerForHall(hall));
            setBlock(world, centerX + 9, y + 2, centerZ, bannerForHall(hall));
            placeStandingSign(world, centerX, y + 1, centerZ - 2, names[hall], subtitles[hall], "plots "
                    + (regionX * 4) + "-" + (regionX * 4 + 3), "z "
                    + (regionZ * 4) + "-" + (regionZ * 4 + 3));
        }
    }

    private void buildEntrance(World world, int originX, int y, int originZ, int canvasSize, int plotSize, int span) {
        int centerX = originX + span / 2;
        int entryZ = originZ - 22;
        for (int dx = -14; dx <= 14; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                boolean edge = Math.abs(dx) == 14 || Math.abs(dz) == 5;
                setBlock(world, centerX + dx, y - 1, entryZ + dz, edge ? Material.GOLD_BLOCK : Material.POLISHED_DEEPSLATE);
            }
        }
        for (int dy = 0; dy <= 8; dy++) {
            setBlock(world, centerX - 12, y + dy, entryZ, Material.DARK_OAK_LOG);
            setBlock(world, centerX + 12, y + dy, entryZ, Material.DARK_OAK_LOG);
        }
        for (int dx = -12; dx <= 12; dx++) {
            setBlock(world, centerX + dx, y + 8, entryZ, Material.GOLD_BLOCK);
        }
        setBlock(world, centerX, y, entryZ + 2, Material.LODESTONE);
        setBlock(world, centerX, y + 1, entryZ + 2, Material.BEACON);
        placeStandingSign(world, centerX - 4, y, entryZ - 2, "YOU ARE HERE", "AfterBlock", "Plot map alive", "Run import");
        placeStandingSign(world, centerX + 4, y, entryZ - 2, "Packet map", "0,0 -> " + originX + "," + originZ,
                (canvasSize - 1) + "," + (canvasSize - 1) + " -> "
                        + (originX + (canvasSize - 1) * plotSize) + "," + (originZ + (canvasSize - 1) * plotSize),
                "size " + plotSize);
        placeStandingSign(world, centerX, y, entryZ + 7, "Route trail", "import relic", "then follow", "lit floor");
    }

    private void placeLivingRoute(World world, Location base, String title, String owner, String hall) {
        int originX = galleryOriginX();
        int originZ = galleryOriginZ();
        int canvasSize = canvasSize();
        int plotSize = plotSize();
        int span = (canvasSize - 1) * plotSize;
        int y = base.getBlockY();
        int centerX = originX + span / 2;
        int entryZ = originZ - 18;
        int targetX = base.getBlockX();
        int targetZ = base.getBlockZ();
        int plotX = plotIndexForWorld(targetX, originX, plotSize, canvasSize);
        int plotZ = plotIndexForWorld(targetZ, originZ, plotSize, canvasSize);
        Material accent = hallAccent(hallIndexForPlot(plotX, plotZ));

        drawRouteLine(world, centerX, entryZ, targetX, entryZ, y - 1, accent);
        drawRouteLine(world, targetX, entryZ, targetX, targetZ, y - 1, accent);
        setBlock(world, centerX, y, entryZ, Material.SEA_LANTERN);
        setBlock(world, targetX, y, entryZ, Material.SEA_LANTERN);
        setBlock(world, targetX, y, targetZ + 5, Material.GLOWSTONE);
        placeStandingSign(world, centerX - 5, y, entryZ + 2, "Route alive", "last import", "plot " + plotX + "," + plotZ, "follow lights");
        placeStandingSign(world, targetX - 6, y, targetZ + 4, "Arrived", title, owner, hall);
    }

    private void drawRouteLine(World world, int startX, int startZ, int endX, int endZ, int y, Material accent) {
        int x = startX;
        int z = startZ;
        int dx = Integer.compare(endX, startX);
        int dz = Integer.compare(endZ, startZ);
        int steps = 0;
        while (true) {
            Material marker = steps % 8 == 0 ? Material.SEA_LANTERN : accent;
            setBlock(world, x, y, z, marker);
            if (x == endX && z == endZ) {
                break;
            }
            if (x != endX) {
                x += dx;
            }
            if (z != endZ) {
                z += dz;
            }
            steps++;
        }
    }

    private int plotIndexForWorld(int coordinate, int origin, int plotSize, int canvasSize) {
        int plot = Math.round((coordinate - origin) / (float) plotSize);
        return Math.max(0, Math.min(canvasSize - 1, plot));
    }

    private void placePlotSign(World world, int x, int y, int z, int plotX, int plotZ) {
        placeStandingSign(world, x + 6, y, z + 4, "Plot " + plotX + "," + plotZ, "XYZ " + x + " " + y, "Z " + z, "packet lands here");
    }

    private void placeStandingSign(World world, int x, int y, int z, String line0, String line1, String line2, String line3) {
        Block block = world.getBlockAt(x, y, z);
        block.setType(Material.OAK_SIGN, false);
        if (block.getState() instanceof Sign sign) {
            sign.setLine(0, trimLine(line0));
            sign.setLine(1, trimLine(line1));
            sign.setLine(2, trimLine(line2));
            sign.setLine(3, trimLine(line3));
            sign.update();
        }
    }

    private int hallIndexForPlot(int plotX, int plotZ) {
        return Math.min(2, plotX / 4) + Math.min(2, plotZ / 4) * 3;
    }

    private Material hallAccent(int hall) {
        Material[] accents = {
                Material.YELLOW_TERRACOTTA, Material.LIME_TERRACOTTA, Material.RED_TERRACOTTA,
                Material.BLUE_TERRACOTTA, Material.PINK_TERRACOTTA, Material.LIGHT_GRAY_TERRACOTTA,
                Material.PURPLE_TERRACOTTA, Material.ORANGE_TERRACOTTA, Material.GREEN_TERRACOTTA
        };
        return accents[Math.floorMod(hall, accents.length)];
    }

    private Material bannerForHall(int hall) {
        Material[] banners = {
                Material.YELLOW_BANNER, Material.LIME_BANNER, Material.RED_BANNER,
                Material.BLUE_BANNER, Material.PINK_BANNER, Material.LIGHT_GRAY_BANNER,
                Material.PURPLE_BANNER, Material.ORANGE_BANNER, Material.GREEN_BANNER
        };
        return banners[Math.floorMod(hall, banners.length)];
    }

    private void setBlock(World world, int x, int y, int z, Material material) {
        world.getChunkAt(x >> 4, z >> 4).load(true);
        world.getBlockAt(x, y, z).setType(material, false);
    }

    private int canvasSize() {
        return Math.max(1, getConfig().getInt("canvas-size", 12));
    }

    private int plotSize() {
        return Math.max(8, getConfig().getInt("plot-size", 32));
    }

    private int galleryOriginX() {
        return getConfig().getInt("gallery-origin.x", -192);
    }

    private int galleryOriginY() {
        return getConfig().getInt("gallery-origin.y", 80);
    }

    private int galleryOriginZ() {
        return getConfig().getInt("gallery-origin.z", -192);
    }

    private String get(String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(12))
                .header("User-Agent", "DreamWall-Paper-Bridge/0.1")
                .GET()
                .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IOException("HTTP " + response.statusCode() + " from " + url);
        }
        return response.body();
    }

    private String post(String url, String body) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(18))
                .header("User-Agent", "DreamWall-Paper-Bridge/0.1")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IOException("HTTP " + response.statusCode() + " from " + url);
        }
        return response.body();
    }

    private Material materialFromPacket(JsonObject minecraft) {
        JsonArray materials = minecraft.has("materials") && minecraft.get("materials").isJsonArray()
                ? minecraft.getAsJsonArray("materials")
                : new JsonArray();
        for (JsonElement element : materials) {
            String name = element.getAsString().toUpperCase(Locale.ROOT).replace("MINECRAFT:", "");
            Material material = Material.matchMaterial(name);
            if (material != null && material.isBlock()) {
                return material;
            }
        }
        return Material.POLISHED_DEEPSLATE;
    }

    private String text(JsonObject object, String key, String fallback) {
        if (object == null || !object.has(key) || object.get(key).isJsonNull()) {
            return fallback;
        }
        return object.get(key).getAsString();
    }

    private int integer(JsonObject object, String key, int fallback) {
        if (object == null || !object.has(key) || object.get(key).isJsonNull()) {
            return fallback;
        }
        return object.get(key).getAsInt();
    }

    private int number(JsonObject object, String key, int fallback) {
        return integer(object, key, fallback);
    }

    private String trimLine(String value) {
        String cleaned = value == null ? "" : value.replaceAll("\\s+", " ").trim();
        return cleaned.length() <= 15 ? cleaned : cleaned.substring(0, 15);
    }

    private ItemStack artifactItem(String name, int customModelData) {
        return artifactItem(name, customModelData, List.of());
    }

    private ItemStack artifactItem(String name, int customModelData, List<String> lore) {
        ItemStack item = new ItemStack(Material.PAPER);
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            meta.setDisplayName(compactItemName(name));
            meta.setCustomModelData(customModelData);
            if (!lore.isEmpty()) {
                meta.setLore(lore.stream().map(this::compactLore).toList());
            }
            item.setItemMeta(meta);
        }
        return item;
    }

    private ItemStack routeCompass(String title, String owner, String hall, Location base) {
        ItemStack compass = new ItemStack(Material.COMPASS);
        ItemMeta meta = compass.getItemMeta();
        if (meta != null) {
            meta.setDisplayName("Route to " + compactItemName(title));
            meta.setLore(List.of(
                    compactLore("Owner: " + owner),
                    compactLore("Hall: " + hall),
                    compactLore("XYZ: " + base.getBlockX() + " " + base.getBlockY() + " " + base.getBlockZ()),
                    "Follow the lit floor from YOU ARE HERE."));
            compass.setItemMeta(meta);
        }
        return compass;
    }

    private void placeDisplayRelic(World world, Location base, ItemStack item) {
        Location displayLocation = base.clone().add(0.5, 1.85, 0.5);
        world.spawn(displayLocation, ItemDisplay.class, display -> {
            display.setItemStack(item.clone());
            display.setBillboard(Billboard.CENTER);
            display.setRotation(0, 0);
            display.setGlowing(true);
        });
    }

    private ItemStack passportBook(String title, String owner, String hall, String zone, String memory, String spirit,
            String command, Location base, int customModelData) {
        ItemStack book = new ItemStack(Material.WRITTEN_BOOK);
        if (book.getItemMeta() instanceof BookMeta meta) {
            meta.setTitle(compactBookTitle(title));
            meta.setAuthor(owner == null || owner.isBlank() ? "AfterBlock Museum" : owner);
            meta.setDisplayName(compactItemName(title) + " Passport");
            meta.setPages(
                    bookPage("AFTERBLOCK PASSPORT", title, owner, hall, zone,
                            "XYZ " + base.getBlockX() + " " + base.getBlockY() + " " + base.getBlockZ(),
                            "CMD " + customModelData),
                    bookPage("HISTORY", memory, "", "SPIRIT", spirit),
                    bookPage("MINECRAFT RELIC", command, "", "Use /dreamwall pack if the item still looks like paper."));
            book.setItemMeta(meta);
        }
        return book;
    }

    private void placePassportLectern(World world, Location base, ItemStack passport) {
        Block lecternBlock = base.clone().add(1, 1, 0).getBlock();
        lecternBlock.setType(Material.LECTERN);
        if (lecternBlock.getState() instanceof Lectern lectern) {
            lectern.getInventory().setItem(0, passport.clone());
            lectern.update();
        }
    }

    private void placeSpiritButton(World world, Location base, String title, String owner, String hall, String memory, String spirit) {
        Location anchor = base.clone().add(-1, 0, 0);
        setBlock(world, anchor.getBlockX(), anchor.getBlockY(), anchor.getBlockZ(), Material.GILDED_BLACKSTONE);
        Block buttonBlock = anchor.clone().add(0, 1, 0).getBlock();
        buttonBlock.setType(Material.WARPED_BUTTON, false);
        if (buttonBlock.getBlockData() instanceof Switch button) {
            button.setFace(Switch.Face.FLOOR);
            button.setFacing(BlockFace.NORTH);
            buttonBlock.setBlockData(button, false);
        }

        Location buttonLocation = buttonBlock.getLocation();
        String key = spiritButtonKey(buttonLocation);
        getConfig().set(key + ".title", title);
        getConfig().set(key + ".owner", owner);
        getConfig().set(key + ".hall", hall);
        getConfig().set(key + ".memory", memory);
        getConfig().set(key + ".spirit", spirit);
        getConfig().set(key + ".xyz", base.getBlockX() + " " + base.getBlockY() + " " + base.getBlockZ());
        saveConfig();
        placeStandingSign(world, base.getBlockX() - 4, base.getBlockY(), base.getBlockZ() - 2,
                "Spirit button", "right-click", "profile + lore", compactItemName(title));
    }

    private String spiritButtonKey(Location location) {
        String worldName = location.getWorld() == null ? "world" : location.getWorld().getName();
        String safeWorld = worldName.replaceAll("[^A-Za-z0-9_-]", "_");
        return "spirit-buttons." + safeWorld + "_" + location.getBlockX() + "_" + location.getBlockY() + "_" + location.getBlockZ();
    }

    private String giveCommand(int customModelData) {
        return "/give @p minecraft:paper[minecraft:custom_model_data=" + customModelData + "] 1";
    }

    private String compactItemName(String value) {
        String cleaned = value == null ? "AfterBlock Relic" : value.replaceAll("\\s+", " ").trim();
        return cleaned.length() <= 48 ? cleaned : cleaned.substring(0, 47).trim();
    }

    private String compactBookTitle(String value) {
        String cleaned = compactItemName(value);
        return cleaned.length() <= 32 ? cleaned : cleaned.substring(0, 31).trim();
    }

    private String compactLore(String value) {
        String cleaned = value == null ? "" : value.replaceAll("\\s+", " ").trim();
        return cleaned.length() <= 72 ? cleaned : cleaned.substring(0, 71).trim();
    }

    private String bookPage(String... lines) {
        String page = String.join("\n", lines).replaceAll("\\n{3,}", "\n\n").trim();
        return page.length() <= 640 ? page : page.substring(0, 637).trim() + "...";
    }

    private String spaceUrl() {
        return getConfig().getString("space-url", "https://build-small-hackathon-dreamwall-mc.hf.space").replaceAll("/+$", "");
    }

    private String resourcePackUrl() {
        return getConfig().getString("resource-pack-url",
                "https://huggingface.co/spaces/build-small-hackathon/dreamwall-mc/resolve/main/resource-pack/AfterBlockMuseum.zip");
    }

    private String resourcePackSha1() {
        return getConfig().getString("resource-pack-sha1", "03487f018e2062e254b5ea443396f29d099f8b67");
    }

    private byte[] resourcePackSha1Bytes() {
        String hex = resourcePackSha1().replaceAll("[^0-9a-fA-F]", "");
        if (hex.length() != 40) {
            return new byte[0];
        }
        byte[] bytes = new byte[20];
        for (int i = 0; i < bytes.length; i++) {
            bytes[i] = (byte) Integer.parseInt(hex.substring(i * 2, i * 2 + 2), 16);
        }
        return bytes;
    }
}
