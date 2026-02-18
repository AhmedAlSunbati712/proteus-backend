import authenticationMiddleware from "../middleware/auth";
import userController from "../controllers/user";
import { Router } from "express";
import { Request } from "express";

const router = Router();

router.post("/signup", userController.createUser);
router.post("/login", userController.loginUser);
router.post("/logout", userController.logoutUser);
router.get("/", authenticationMiddleware, async (req, res) => {
    await userController.getUser(req as Request & { userId: string }, res);
});
router.put("/", authenticationMiddleware, async (req, res) => {
    await userController.updateUser(req as Request & { userId: string }, res);
});
router.delete("/", authenticationMiddleware, async (req, res) => {
    await userController.deleteUser(req as Request & {userId: string}, res);
});

export default router;