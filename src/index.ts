import "./utils/env";
import { PORT } from "./utils/env"; 
import express from "express";
import routers from "./routers/routers";
import cookieParser from "cookie-parser";
const app = express();

app.use(express.json());
app.use(cookieParser());


app.get("/", (_req, res) => {
  res.json({ message: "Welcome to Proteus Backend!" });
})

app.use("/images", routers.imagesRouter);
app.use("/user", routers.userRouter);
app.get("/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
