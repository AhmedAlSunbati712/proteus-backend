import dotenv from "dotenv";
dotenv.config();

const PORT = Number(process.env.PORT) || 3000;
const DATABASE_URL = process.env.DATABASE_URL ?? "postgresql://proteus:proteus@localhost:5432/proteus";
const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379";

if (!process.env.DATABASE_URL && process.env.NODE_ENV !== "development") {
  throw new Error("DATABASE_URL is required");
}

export { PORT, DATABASE_URL, REDIS_URL };
