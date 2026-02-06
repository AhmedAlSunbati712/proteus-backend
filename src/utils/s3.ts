import { s3Client, S3_BUCKET } from "../config/s3";
import { PutObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const UPLOADS_PREFIX = "uploads";

const sanitizeSegment = (s: string): string => s.replace(/[/\\]/g, "_").trim() || "file";

const generateKey = (userId: string, fileType: string, fileName: string): string => {
    const safeName = sanitizeSegment(fileName);
    const safeType = sanitizeSegment(fileType);
    return `${UPLOADS_PREFIX}/${userId}/${safeName}.${safeType}/${Date.now()}`;
};


const getPresignedUploadUrl = async (key: string): Promise<string> => {
    const command = new PutObjectCommand({
        Bucket: S3_BUCKET,
        Key: key,
    });
    return await getSignedUrl(s3Client, command, { expiresIn: 60 * 15 });
};

const getPresignedDownloadUrl = async (key: string): Promise<string> => {
    const command = new GetObjectCommand({
        Bucket: S3_BUCKET,
        Key: key,
    });
    return await getSignedUrl(s3Client, command, { expiresIn: 60 * 60 });
};

const uploadFile = async (key: string, file: Buffer): Promise<void> => {
    const command = new PutObjectCommand({
        Bucket: S3_BUCKET,
        Key: key,
        Body: file,
    });
    await s3Client.send(command);
}

const downloadFile = async (key: string): Promise<Buffer> => {
    const command = new GetObjectCommand({
        Bucket: S3_BUCKET,
        Key: key,
    });
    const response = await s3Client.send(command);
    if (!response.Body) {
        throw new Error("S3 object has no body");
    }
    const bytes = await response.Body.transformToByteArray();
    return Buffer.from(bytes);
};

const isKeyAllowedForUser = (key: string, userId: string): boolean => {
    const prefix = `${UPLOADS_PREFIX}/${userId}/`;
    return key.startsWith(prefix);
};

const s3Utils = {
    getPresignedUploadUrl,
    getPresignedDownloadUrl,
    uploadFile,
    downloadFile,
    generateKey,
    isKeyAllowedForUser,
}
export default s3Utils;