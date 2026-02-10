import vtonService from '../services/vton';
import { Request, Response } from 'express';

const getVTONs = async (req: Request & {user_id: string}, res: Response) => {
    try {
        const user_id = req.user_id; // Assuming user ID is available in the request object
        const query = req.query;
        const vtons = await vtonService.getVTONs(user_id, query);
        res.status(200).json(vtons);
    } catch (error) {
        res.status(500).json({ error: "Failed to fetch VTONs" });
    }
}

const createVTON = async (req: Request & {user_id: string}, res: Response) => {
    try {
        const user_id = req.user_id;
        const vtonData = req.body;
        const newVTON = await vtonService.createVTON(user_id, vtonData);
        res.status(201).json(newVTON);
    } catch (error) {
        res.status(500).json({ error: "Failed to create VTON" });
    }
}

const updateVTON = async (req: Request & {user_id: string}, res: Response) => {
    try {
        const user_id = req.user_id;
        const vton_id = req.params.id as string;
        const updateData = req.body;
        const updatedVTON = await vtonService.updateVTON(user_id, vton_id, updateData);
        res.status(200).json(updatedVTON);
    } catch (error) {
        res.status(500).json({ error: "Failed to update VTON" });
    }
}

const deleteVTON = async (req: Request & {user_id: string}, res: Response) => {
    try {
        const user_id = req.user_id;
        const vton_id = req.params.id as string;
        await vtonService.deleteVTON(user_id, vton_id);
        res.status(204).send();
    } catch (error) {
        res.status(500).json({ error: "Failed to delete VTON" });
    }
}

const vtonController = {
    getVTONs,
    createVTON,
    updateVTON,
    deleteVTON,
};

export default vtonController;