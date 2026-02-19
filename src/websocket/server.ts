import type { Server as HttpServer } from "http";
import jwt from "jsonwebtoken";
import { WebSocket } from "ws";
import { Server } from "ws";
import { subscriber } from "../config/redis";
import vtonService from "../services/vton";

const JWT_SECRET = process.env.JWT_SECRET || "secret";

interface JobDoneEvent {
  job_id: string;
  job_type: "tailor" | "try_on";
  status: "done" | "failed";
  user_id: string;
  vton_id: string;
  result_s3_key: string | null;
  error: string | null;
  finished_at: string;
}

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
  try {
    await subscriber.subscribe("events:job_done");
  } catch (error) {
    console.error("Failed to subscribe to events:job_done channel:", error);
    process.exit(1);
  }

  subscriber.on("message", async (channel, message) => {
    if (channel !== "events:job_done") return;

    let payload: JobDoneEvent;
    try {
      payload = JSON.parse(message) as JobDoneEvent;
    } catch (error) {
      console.error("Failed to parse events:job_done payload:", error);
      return;
    }

    const { user_id, vton_id, job_type, status, result_s3_key } = payload;

    if (status === "done" && result_s3_key) {
      try {
        if (job_type === "try_on") {
          await vtonService.updateVTON(user_id, vton_id, { outfit_try_on: result_s3_key });
        }
        if (job_type === "tailor") {
          await vtonService.updateVTON(user_id, vton_id, { cleaned_outfit: result_s3_key });
        }
      } catch (error) {
        console.error("Failed to update VTON from job_done event:", error);
      }
    }

    const targetSocket = usersToSockets.get(user_id);
    if (!targetSocket || targetSocket.readyState !== WebSocket.OPEN) return;
    targetSocket.send(JSON.stringify(payload));
  });

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

