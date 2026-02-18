import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import dotenv from "dotenv";
dotenv.config();

const JWT_SECRET = process.env.JWT_SECRET ?? "secret";

const authenticationMiddleware = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
        const token = req.headers.authorization?.split(" ")[1] || req.cookies?.token;
        if (!token) {
            res.status(401).json({ message: "Unauthorized" });
            return;
        }
        const decoded = jwt.verify(token, JWT_SECRET) as { userId: string };
        (req as any).userId = decoded.userId;
        (req as any).token = token;
        next();
    } catch (error) {
        console.error(error);
        res.status(401).json({ message: "Unauthorized" });
        return;
    }
}

export default authenticationMiddleware;