package com.dreamwall;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
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
import org.bukkit.block.Sign;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

public final class DreamWallPlugin extends JavaPlugin {
    private HttpClient httpClient;
    private BukkitTask pollTask;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(8))
                .build();

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

        sender.sendMessage("DreamWall bridge is configured for: " + spaceUrl());
        sender.sendMessage("Canvas: " + getConfig().getInt("canvas-size", 12) + "x" + getConfig().getInt("canvas-size", 12)
                + " plots, plot size=" + getConfig().getInt("plot-size", 32));
        sender.sendMessage("Use /dreamwall fetch to test Hugging Face reachability.");
        sender.sendMessage("Use /dreamwall demo in-game to place a safe AfterBlock pedestal proof.");
        sender.sendMessage("Use /dreamwall import or /dreamwall import here to place a live Space artifact packet.");
        return true;
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
                sender.sendMessage("Next step: call /gradio_api/call/curate_artifact and import dreamwall.museum.v1.");
                sender.sendMessage("Use /dreamwall demo for a local pedestal proof with custom model data.");
            } catch (IOException | InterruptedException e) {
                sender.sendMessage("DreamWall fetch failed: " + e.getMessage());
                Thread.currentThread().interrupt();
            }
        });
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
        String payload = "{\"data\":[\"Minecraft\",\"@afterblock\",\"object_photo\",\"a white AirPods case from a first year desk\",\"A small object that carried private worlds through public noise.\",null]}";
        String callBody = post(spaceUrl() + "/gradio_api/call/curate_artifact", payload);
        JsonObject call = JsonParser.parseString(callBody).getAsJsonObject();
        String eventId = call.get("event_id").getAsString();
        String stream = get(spaceUrl() + "/gradio_api/call/curate_artifact/" + eventId);
        for (String line : stream.split("\\R")) {
            if (line.startsWith("data: ")) {
                JsonArray outputs = JsonParser.parseString(line.substring(6)).getAsJsonArray();
                JsonObject packet = JsonParser.parseString(outputs.get(5).getAsString()).getAsJsonObject();
                String type = text(packet, "type", "");
                if (!"dreamwall.museum.v1".equals(type)) {
                    throw new IOException("unexpected packet type " + type);
                }
                return packet;
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

        Material pedestalMaterial = materialFromPacket(minecraft);
        base.getBlock().setType(pedestalMaterial);
        base.clone().add(0, 1, 0).getBlock().setType(Material.AMETHYST_BLOCK);

        Block signBlock = base.clone().add(0, 1, -1).getBlock();
        signBlock.setType(Material.OAK_SIGN);
        String title = text(minecraft, "title", text(artifact, "title", "AfterBlock Relic"));
        String owner = text(minecraft, "owner_handle", text(artifact, "owner_handle", "@unknown"));
        String hall = text(minecraft, "hall", text(artifact, "hall", "Museum"));
        String plaque = text(minecraft, "plaque_text", text(artifact, "plaque_line", "Preserved in AfterBlock"));
        if (signBlock.getState() instanceof Sign sign) {
            sign.setLine(0, trimLine(title));
            sign.setLine(1, trimLine(owner));
            sign.setLine(2, trimLine(hall));
            sign.setLine(3, trimLine(plaque));
            sign.update();
        }

        ItemStack item = new ItemStack(Material.PAPER);
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            meta.setDisplayName(trimLine(title) + " Passport");
            int customModelData = integer(minecraft, "custom_model_data", 730001);
            meta.setCustomModelData(customModelData);
            item.setItemMeta(meta);
        }
        player.getInventory().addItem(item);
        world.spawnParticle(Particle.ENCHANT, base.clone().add(0.5, 1.4, 0.5), 38, 0.45, 0.65, 0.45, 0.015);
        player.sendMessage("Imported " + title + " by " + owner + " into " + hall + ".");
        player.sendMessage("Gave Paper item with CustomModelData " + integer(minecraft, "custom_model_data", 730001) + ".");
        if (!placeHere) {
            player.sendMessage("Placed at packet coordinates " + base.getBlockX() + " " + base.getBlockY() + " " + base.getBlockZ()
                    + ". Use /dreamwall import here for a nearby proof.");
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

        ItemStack item = new ItemStack(Material.PAPER);
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            meta.setDisplayName("AfterBlock Artifact Passport");
            meta.setCustomModelData(730002);
            item.setItemMeta(meta);
        }
        player.getInventory().addItem(item);
        world.spawnParticle(Particle.ENCHANT, base.clone().add(0.5, 1.4, 0.5), 28, 0.35, 0.55, 0.35, 0.01);
        sender.sendMessage("Placed demo AfterBlock pedestal and gave Paper item with CustomModelData 730002.");
        sender.sendMessage("Install the AfterBlockMuseum resource pack to see the generated item texture.");
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

    private String spaceUrl() {
        return getConfig().getString("space-url", "https://build-small-hackathon-dreamwall-mc.hf.space").replaceAll("/+$", "");
    }
}
