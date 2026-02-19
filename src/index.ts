import "./utils/env";
import { PORT } from "./utils/env";
import express from "express";
import routers from "./routers/routers";
import cookieParser from "cookie-parser";
import { createServer } from "http";
import { initWebSocket } from "./websocket/server";
import cors from "cors";
import morgan from "morgan";


const app = express();
export const server = createServer(app);

app.use(express.json());
app.use(morgan("dev"));
app.use(cookieParser());
app.use(cors({
  origin: process.env.FRONTEND_URL || "http://localhost:5173",
  credentials: true,
}));
app.get("/", (_req, res) => {
  res.json({ message: "Welcome to Proteus Backend!" });
});

app.use("/images", routers.imagesRouter);
app.use("/user", routers.userRouter);
app.use("/vton", routers.vtonRouter);
app.use("/jobs", routers.jobsRouter);

app.get("/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

(async () => {
  try {
    await initWebSocket(server);
  } catch (err) {
    console.error("Failed to initialize WebSocket (Redis may be down):", err);
    process.exit(1);
  }
  server.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
  });
})();
