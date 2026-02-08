import type { Server as HttpServer } from "http";
import jwt from "jsonwebtoken";
import { WebSocket } from "ws";
import { Server } from "ws";
import { subscriber } from "../config/redis";

const JWT_SECRET = process.env.JWT_SECRET || "secret";

function getTokenFromRequest(req: { url?: string; headers: Record<string, string | string[] | undefined> }): string | null {
  const auth = req.headers.authorization;
  const authStr = Array.isArray(auth) ? auth[0] : auth;
  if (authStr?.startsWith("Bearer ")) {
    return authStr.slice(7);
  }
  const url = new URL(req.url || "", `http://${req.headers.host}`);
  const tokenFromQuery = url.searchParams.get("token");
  if (tokenFromQuery) return tokenFromQuery;
  const cookieHeader = req.headers.cookie;
  const cookieStr = Array.isArray(cookieHeader) ? cookieHeader[0] : cookieHeader;
  if (cookieStr) {
    const match = cookieStr.split(";").find((c: string) => c.trim().startsWith("token="));
    if (match) return match.split("=")[1]?.trim() ?? null;
  }
  return null;
}

export async function initWebSocket(server: HttpServer): Promise<void> {
  const wss = new Server({ server, path: "/ws" });

  // Storing user id's and their corresponding websockets for communication
  const usersToSockets = new Map<string, WebSocket>();

  // Listening on the events:job_done channel
  await subscriber.subscribe("events:job_done");

  // TODO: Handle redis channel messages here.

  wss.on("connection", (ws: WebSocket, req) => {
    const token = getTokenFromRequest(req);
    if (!token) {
      ws.close(4401, "Unauthorized");
      return;
    }
    let userId: string;
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as { userId: string };
      userId = decoded.userId;
    } catch {
      ws.close(4401, "Unauthorized");
      return;
    }
    usersToSockets.set(userId, ws);
    ws.on("close", () => {
      usersToSockets.delete(userId);
      console.log(`User ${userId} disconnected`);
    });
    console.log(`User ${userId} connected`);
  });
}


