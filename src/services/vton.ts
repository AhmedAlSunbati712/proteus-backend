import { prisma } from '../db/index';
import { VTON } from "@prisma/client";

export const getVTONs = async (user_id: string, query: Partial<VTON>): Promise<VTON[]> => {
    try {
        const vtons = await prisma.vTON.findMany({
            where: {
                user_id,
                ...query,
            }
        });
        return vtons;
    } catch (error) {
        console.error("Error fetching VTONs:", error);
        throw error;
    }
}

const createVTON = async (user_id: string, vtonData: Omit<VTON, 'id' | 'user_id'>): Promise<VTON> => {
    try {
        const newVTON = await prisma.vTON.create({
            data: {
                user_id,
                ...vtonData,
            }
        });
        return newVTON;
    } catch (error) {
        console.error("Error creating VTON:", error);
        throw error;
    }
}

const updateVTON = async (user_id: string, vton_id: string, updateData: Partial<Omit<VTON, 'id' | 'user_id'>>): Promise<VTON> => {
    try {
        const updatedVTON = await prisma.vTON.update({
            where: {
                id: vton_id,
                user_id,
            },
            data: updateData,
        });
        return updatedVTON;
    } catch (error) {
        console.error("Error updating VTON:", error);
        throw error;
    }
}

const deleteVTON = async (user_id: string, vton_id: string): Promise<VTON> => {
    try {
        const deletedVTON = await prisma.vTON.delete({
            where: {
                id: vton_id,
                user_id,
            }
        });
        return deletedVTON;
    } catch (error) {
        console.error("Error deleting VTON:", error);
        throw error;
    }
}

const vtonService = {
    getVTONs,
    createVTON,
    updateVTON,
    deleteVTON,
}

export default vtonService;