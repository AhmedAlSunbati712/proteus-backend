import userService from "../services/user"
import { Request, Response } from "express";
import { generateToken, hashPassword } from "../utils/auth";
import { User } from "@prisma/client";
import { comparePassword } from "../utils/auth";
import jwt from "jsonwebtoken";

const createUser = async (req: Request, res: Response): Promise<void> => {
    try {
        const { user_name, password, email} = req.body;
        if (!user_name || !password || !email) {
            res.status(400).json({ error: "Missing required fields" });
            return;
        }
        const users = await userService.getUsers({email: email} as Partial<User>);
        if (users.length > 0) {
            res.status(400).json({ error: "User already exists" });
            return;
        }
        const hashedPassword = await hashPassword(password);
        const data = {user_name: user_name, password: hashedPassword, email: email};
        const user = await userService.createUser(data);
        const {password: _password, ...userData} = user;
        res.status(201).json(userData);
    } catch (error) {
        res.status(500).json({ error: "Failed to create user" });
    }
}
const loginUser = async (req: Request, res: Response): Promise<void> => {
    try {
        const { email, password } = req.body;
        const users = await userService.getUsers({email: email} as Partial<User>);
        if (users.length === 0) {
            res.status(401).json({ error: "Invalid email or password" });
            return;
        }
        const user = users[0] as User;
        const isPasswordValid = await comparePassword(password, user.password);
        if (!isPasswordValid) {
            res.status(401).json({ error: "Invalid email or password" });
            return;
        }
        const token = generateToken(user.id);
        res.status(200).cookie("token", token, { httpOnly: true, secure: process.env.NODE_ENV === "production", maxAge: 3600000 }).json({ message: "Logged in successfully" });
    } catch (error) {
        res.status(500).json({ error: "Failed to login user" });
    }
}

const getUser = async (req: Request & { userId: string }, res: Response): Promise<void> => {
    try {
        const userId = req.userId;
        const user = await userService.getUser(userId, {});
        res.json(user);
    } catch (error) { 
        console.error(error);
        res.status(500).json({ error: "Failed to get user" });
    }
}

const getUsers = async (req: Request, res: Response): Promise<void> => {
    try {
        const query = req.query as Partial<User>;
        const users = await userService.getUsers(query as Partial<User>);
        res.json(users);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Failed to get users" });
    }
}

const updateUser = async (req: Request &{ userId: string }, res: Response): Promise<void> => {
    try {
        const userId = req.userId;
        const data = req.body as Partial<User>;
        const user = await userService.updateUser(userId, data);
        res.json(user);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Failed to update user" });
    }
}

const deleteUser = async (req: Request & { userId: string }, res: Response): Promise<void> => {
    try {
        const userId = req.userId;
        await userService.deleteUser(userId);
        res.status(204).send();
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Failed to delete user" });
    }
}

const userController = {
    createUser,
    getUser,
    getUsers,
    loginUser,
    updateUser,
    deleteUser,
}

export default userController;