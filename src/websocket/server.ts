import type { Server as HttpServer } from "http";
import { WebSocket } from "ws";
import { Server } from "ws";
import { subscriber } from "../config/redis";

export function initWebSocket(server: HttpServer): void {
  const wss = new Server({ server, path: "/ws" });

  // Storing user id's and their corresponding websockets for communication
  const usersToSockets = new Map<string, WebSocket>();

  // Listening on the events:job_done channel
  subscriber.subscribe("events:job_done");

  // TODO: Handle redis channel messages here.

  wss.on("connection", (ws: WebSocket, req) => {
    const url = new URL(req.url || '', `http://${req.headers.host}`);
    const userId = url.searchParams.get("userId");
    if (!userId) {
      ws.close();
      return;
    }
    // Save the user websocket
    usersToSockets.set(userId, ws);
    ws.on("close", () => {
      if (userId) usersToSockets.delete(userId);
      console.log(`User ${userId} disconnected`);
    });
    console.log(`User ${userId} connected`);
  });
}


