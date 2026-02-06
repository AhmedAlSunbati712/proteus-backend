import "./utils/env";
import { PORT } from "./utils/env"; 
import express from "express";
import routers from "./routers/routers";

const app = express();

app.use(express.json());

app.get("/", (_req, res) => {
  res.json({ message: "Welcome to Proteus Backend!" });
})

app.use("/images", routers.imagesRouter);

app.get("/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
