// components/TransactionStreamer.tsx

import React, { useEffect, useRef, useState } from "react";
import JSZip from "jszip";
import { Button, TextField, Typography, Box, LinearProgress, Alert, Slider } from "@mui/material";

const LOCALSTORAGE_KEY = "tx_endpoint";

// 1. แก้ไข Interface ให้ระบุ Type ที่ถูกต้อง (ตรงกับ Backend Go)
interface TxRecord {
    step: number;
    type: string;
    amount: number;
    nameOrig: string;
    oldbalanceOrg: number;
    newbalanceOrig: number;
    nameDest: string;
    oldbalanceDest: number;
    newbalanceDest: number;
    isFraud: number;
    isFlaggedFraud: number;
}

// Helper Interface สำหรับการ map ข้อมูลดิบ
type RawRecord = { [key: string]: string };

export default function TransactionStreamer() {
    const [endpoint, setEndpoint] = useState<string>(() => {
        try { return localStorage.getItem(LOCALSTORAGE_KEY) || "" } catch { return "" }
    });
    
    // State ใช้ Type ใหม่
    const [records, setRecords] = useState<TxRecord[]>([]);
    const [headers, setHeaders] = useState<string[]>([]);
    const [recordsPerSecond, setRecordsPerSecond] = useState<number>(100);
    const [isStreaming, setIsStreaming] = useState<boolean>(false);
    const [index, setIndex] = useState<number>(0);
    const [sentCount, setSentCount] = useState<number>(0);
    const [lastError, setLastError] = useState<string | null>(null);
    const [progress, setProgress] = useState<number>(0);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [loadProgress, setLoadProgress] = useState<number>(0);

    const intervalRef = useRef<number | null>(null);

    useEffect(() => {
        try { localStorage.setItem(LOCALSTORAGE_KEY, endpoint) } catch { }
    }, [endpoint]);

    useEffect(() => {
        if (recordsPerSecond > 10000) setRecordsPerSecond(10000);
        if (recordsPerSecond < 1) setRecordsPerSecond(1);
    }, [recordsPerSecond]);

    useEffect(() => {
        return () => stopStreaming();
    }, []);

    async function sendBatch(batch: TxRecord[]) {
        if (!endpoint) {
            setLastError("No endpoint configured.");
            setIsStreaming(false);
            return;
        }
        try {
            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // ข้อมูลใน batch ตอนนี้เป็น Number/String ที่ถูกต้องแล้ว
                body: JSON.stringify({ records: batch }),
            });
            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Failed to send batch: ${res.status} ${res.statusText} - ${text}`);
            }
            
            // console.log(batch.length)
            setSentCount(prev => prev + batch.length);
            // ใช้ Functional update เพื่อความแม่นยำของ State records
            setProgress(prev => {
                const currentSent = sentCount + batch.length;
                return (currentSent / records.length) * 100;
            });
            setLastError(null);
        } catch (err: any) {
            console.log(err.message)
            setLastError(err.message || String(err));
            setIsStreaming(false);
        }
    }

    async function fetchAndUnzipFile() {
        setIsLoading(true);
        setLoadProgress(0);
        try {
            // เช็คว่าไฟล์อยู่ใน public/data/transactions.zip จริงหรือไม่
            const response = await fetch("/data/transactions.zip");
            if (!response.ok) throw new Error("Failed to fetch the file.");

            const contentLength = response.headers.get("content-length");
            const totalSize = contentLength ? parseInt(contentLength, 10) : 0;
            let loadedSize = 0;

            const reader = response.body?.getReader();
            const chunks: Array<BlobPart> = [];

            while (reader) {
                const { done, value } = await reader.read();
                if (done) break;
                if (value) {
                    chunks.push(value.buffer);
                    loadedSize += value.length;
                    if (totalSize) {
                        setLoadProgress((loadedSize / totalSize) * 100);
                    }
                }
            }

            const blob = new Blob(chunks);
            const zip = await JSZip.loadAsync(blob);
            const fileNames = Object.keys(zip.files);
            if (fileNames.length === 0) throw new Error("No files found in the zip.");

            const csvFile = fileNames.find(name => name.endsWith(".csv"));
            if (!csvFile) throw new Error("No CSV file found in the zip.");

            const csvText = await zip.file(csvFile)?.async("text");
            if (!csvText) throw new Error("Failed to read the CSV file.");

            parseCSV(csvText);
        } catch (error: any) {
            setLastError(error.message);
        } finally {
            setIsLoading(false);
            setLoadProgress(0);
        }
    }

    // ฟังก์ชันช่วยแก้ชื่อ Header ที่ผิดปกติ
    function cleanHeader(header: string): string {
        const h = header.trim();
        if (h === "isFraudi") return "isFraud"; // แก้คำผิด
        if (h === "sFlaggedFraud") return "isFlaggedFraud"; // แก้คำผิด
        return h;
    }

    function parseCSV(text: string) {
        const rows = text.split("\n");
        if (rows.length === 0) return;

        // 1. จัดการ Header
        const rawHeaders = rows[0].split(",");
        const hdrs = rawHeaders.map(cleanHeader);
        
        // 2. แปลงข้อมูลแต่ละแถวให้ตรง Type
        const recs: TxRecord[] = [];
        
        // เริ่มที่ i=1 เพื่อข้าม Header
        for (let i = 1; i < rows.length; i++) {
            const row = rows[i].split(",");
            if (row.length !== hdrs.length) continue; // ข้ามแถวที่ไม่สมบูรณ์

            // สร้าง Raw Object ก่อน
            const rawObj: any = {};
            hdrs.forEach((header, index) => {
                rawObj[header] = row[index] ? row[index].trim() : "";
            });

            // แปลงเป็น TxRecord ตาม Interface (Convert String -> Number)
            const record: TxRecord = {
                step: parseInt(rawObj.step) || 0,
                type: rawObj.type,
                amount: parseFloat(rawObj.amount) || 0.0,
                nameOrig: rawObj.nameOrig,
                oldbalanceOrg: parseFloat(rawObj.oldbalanceOrg) || 0.0,
                newbalanceOrig: parseFloat(rawObj.newbalanceOrig) || 0.0,
                nameDest: rawObj.nameDest,
                oldbalanceDest: parseFloat(rawObj.oldbalanceDest) || 0.0,
                newbalanceDest: parseFloat(rawObj.newbalanceDest) || 0.0,
                isFraud: parseInt(rawObj.isFraud) || 0,
                isFlaggedFraud: parseInt(rawObj.isFlaggedFraud) || 0
            };

            recs.push(record);
        }

        setHeaders(hdrs);
        setRecords(recs);
        setIndex(0);
        setSentCount(0);
        setProgress(0);
    }

    function startStreaming() {
        if (records.length === 0) {
            setLastError("No records loaded.");
            return;
        }
        setIsStreaming(true);
        setLastError(null);
        // ไม่ต้อง reset sentCount เพื่อให้ stream ต่อจากเดิมได้ถ้ากด stop แล้ว start ใหม่
        // หรือถ้าอยากเริ่มใหม่เสมอให้ uncomment บรรทัดล่าง
        // setSentCount(0); setIndex(0); 
        
        intervalRef.current = window.setInterval(async () => {
            // ใช้ Functional update เพื่อให้ได้ค่า index ล่าสุดเสมอใน interval
            setIndex((prevIndex) => {
                const end = Math.min(records.length, prevIndex + recordsPerSecond);
                
                // ถ้าส่งครบแล้ว
                if (prevIndex >= records.length) {
                    stopStreaming();
                    return prevIndex;
                }

                const batch = records.slice(prevIndex, end);
                
                // เรียก sendBatch (ไม่ต้อง await ในนี้เพื่อให้ Interval เดินต่อตามเวลาจริง แต่ระวัง Race Condition เล็กน้อย)
                // เพื่อความชัวร์เราจะยิงแล้วปล่อย (Fire and Forget) ใน Interval นี้
                sendBatch(batch);

                return end;
            });
        }, 1000);
    }

    function stopStreaming() {
        setIsStreaming(false);
        if (intervalRef.current) {
            window.clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    }

    return (
        <Box sx={{ padding: 4, maxWidth: 800, margin: "0 auto" }}>
            <Typography variant="h4" gutterBottom>Transaction Streamer</Typography>

            <Box sx={{ marginBottom: 2 }}>
                <TextField
                    label="Endpoint URL"
                    value={endpoint}
                    onChange={(e) => setEndpoint(e.target.value)}
                    fullWidth
                    margin="normal"
                    helperText="Example: http://localhost:3001/api/transactions (Note: Use browser accessible URL)"
                />
            </Box>

            <Box sx={{ marginBottom: 2 }}>
                <Button
                    variant="contained"
                    onClick={fetchAndUnzipFile}
                    disabled={isLoading}
                >
                    {isLoading ? `Loading... ${loadProgress.toFixed(0)}%` : "Load Transactions"}
                </Button>
            </Box>

            {headers.length > 0 && (
                <Box sx={{ marginBottom: 2 }}>
                    <Typography variant="h6" gutterBottom>Transaction Records Preview</Typography>
                    <Box sx={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                            <thead>
                                <tr>
                                    {headers.map((header, index) => (
                                        <th key={index} style={{ border: "1px solid #ddd", padding: "4px", textAlign: "left", backgroundColor: "#f4f4f4" }}>
                                            {header}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {records.slice(0, 5).map((record, rowIndex) => (
                                    <tr key={rowIndex}>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.step}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.type}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.amount}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.nameOrig}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.oldbalanceOrg}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.newbalanceOrig}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.nameDest}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.oldbalanceDest}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.newbalanceDest}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.isFraud}</td>
                                        <td style={{border:"1px solid #ddd", padding:"4px"}}>{record.isFlaggedFraud}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </Box>
                    <Typography variant="body2" color="textSecondary" sx={{ marginTop: 1 }}>
                        Showing first 5 records out of {records.length.toLocaleString()} loaded.
                    </Typography>
                </Box>
            )}

            <Box sx={{ marginBottom: 2 }}>
                <Typography gutterBottom>Transactions per Second: {recordsPerSecond}</Typography>
                <Slider
                    value={recordsPerSecond}
                    onChange={(e, value) => setRecordsPerSecond(value as number)}
                    min={1}
                    max={10000}
                    step={100}
                    valueLabelDisplay="auto"
                />
            </Box>

            {lastError && (
                <Alert severity="error" sx={{ marginBottom: 2 }}>{lastError}</Alert>
            )}

            <Box sx={{ marginBottom: 2 }}>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={startStreaming}
                    disabled={isStreaming}
                >Start Streaming</Button>
                <Button
                    variant="outlined"
                    color="secondary"
                    onClick={stopStreaming}
                    disabled={!isStreaming}
                    sx={{ marginLeft: 2 }}
                >Stop Streaming</Button>
            </Box>

            <Box sx={{ marginBottom: 2 }}>
                <LinearProgress variant="determinate" value={(sentCount / records.length) * 100} />
                <Typography variant="body2" align="center" sx={{mt: 1}}>
                    Records Sent: {sentCount.toLocaleString()} / {records.length.toLocaleString()}
                </Typography>
            </Box>
        </Box>
    );
}