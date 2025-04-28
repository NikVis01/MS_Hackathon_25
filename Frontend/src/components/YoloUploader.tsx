import React, { useState } from "react";

export default function YoloUploader() {
  const [image, setImage] = useState<string | null>(null);
  const [detections, setDetections] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Convert file to base64
  const toBase64 = (file: File) =>
    new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.split(",")[1]);
      };
      reader.onerror = (error) => reject(error);
    });

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setError("");
    setDetections([]);
    const file = e.target.files?.[0];
    if (!file) return;
    setImage(URL.createObjectURL(file));
    setLoading(true);
    try {
      const base64 = await toBase64(file);
      const res = await fetch("http://localhost:8000/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_data: base64 }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "Detection failed");
      setDetections(data.detections);
    } catch (err: any) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto p-4 bg-white rounded shadow">
      <h2 className="text-xl font-bold mb-2">YOLOv8 Image Detection</h2>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      {image && (
        <div className="my-4">
          <img src={image} alt="Uploaded" className="max-w-full max-h-64" />
        </div>
      )}
      {loading && <p>Detecting...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {detections.length > 0 && (
        <div>
          <h3 className="font-semibold">Detections:</h3>
          <ul>
            {detections.map((det, idx) => (
              <li key={idx}>
                <b>{det.class}</b> (conf: {det.confidence.toFixed(2)}) — bbox: [{det.bbox.map((n: number) => n.toFixed(0)).join(", ")}]
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
} 