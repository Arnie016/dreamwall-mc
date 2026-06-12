package com.dreamwall;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.logging.Level;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.Sign;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.ItemFrame;
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

        sender.sendMessage("DreamWall bridge is configured for: " + spaceUrl());
        sender.sendMessage("Canvas: " + getConfig().getInt("canvas-size", 12) + "x" + getConfig().getInt("canvas-size", 12)
                + " plots, plot size=" + getConfig().getInt("plot-size", 32));
        sender.sendMessage("Use /dreamwall fetch to test Hugging Face reachability.");
        sender.sendMessage("Use /dreamwall demo in-game to place a safe AfterBlock pedestal proof.");
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

    private String spaceUrl() {
        return getConfig().getString("space-url", "https://build-small-hackathon-dreamwall-mc.hf.space").replaceAll("/+$", "");
    }
}
