import { prisma } from "../db";
import { Prisma, User } from ".prisma/client";

const getUser = async (userId: string, query: Partial<User>): Promise<User | null> => {
    try {
        return await prisma.user.findUnique({
            where: {
                id: userId,
                ...query,
            },
            include: {
                vtons: true,
            }
        });
    } catch (error) {
        console.error(error);
        throw new Error("Failed to get user");
    }
}

const createUser = async (data: Prisma.UserCreateInput): Promise<User> => {
    try {
        return await prisma.user.create({
            data,
        });
    } catch (error) {
        console.error(error);
        throw new Error("Failed to create user");
    }
}

const getUsers = async (query: Partial<User>): Promise<User[]> => {
    try {
        return await prisma.user.findMany({
            where: {
                ...query,
            },
        });
    } catch (error) {
        console.error(error);
        throw new Error("Failed to get users");
    }
}
const updateUser = async (userId: string, data: Prisma.UserUpdateInput): Promise<User> => {
    try {
        return await prisma.user.update({
            where: { id: userId },
            data,
        });
    } catch (error) {
        console.error(error);
        throw new Error("Failed to update user");
    }
}

const deleteUser = async (userId: string): Promise<void> => {
    try {
        await prisma.user.delete({
            where: { id: userId },
        });
    } catch (error) {
        console.error(error);
        throw new Error("Failed to delete user");
    }
}

const userService = {
    getUser,
    getUsers,
    createUser,
    updateUser,
    deleteUser,

}
export default userService;