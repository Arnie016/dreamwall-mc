package com.dreamwall;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.logging.Level;

import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
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

        sender.sendMessage("DreamWall bridge is configured for: " + spaceUrl());
        sender.sendMessage("Use /dreamwall fetch to test Hugging Face reachability.");
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
                sender.sendMessage("Next step: call /gradio_api/call/generate_art and place row_runs.");
            } catch (IOException | InterruptedException e) {
                sender.sendMessage("DreamWall fetch failed: " + e.getMessage());
                Thread.currentThread().interrupt();
            }
        });
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
