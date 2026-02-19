import s3Utils from "../utils/s3";

const getPresignedUploadUrl = async (userId: string, fileType: string, fileName: string): Promise<{url: string, key: string}> => {
    try {
        const key = s3Utils.generateKey(userId, fileType, fileName);
        const url = await s3Utils.getPresignedUploadUrl(key);

        return {url, key};
    } catch (error) {
        throw new Error("Failed to get presigned upload URL");
    }
};

const getPresignedDownloadUrl = async (key: string): Promise<string> => {
    try {
        return await s3Utils.getPresignedDownloadUrl(key);
    } catch (error) {
        throw new Error("Failed to get presigned download URL");
    }
};

const imageService = {
    getPresignedUploadUrl,
    getPresignedDownloadUrl,
}
export default imageService;