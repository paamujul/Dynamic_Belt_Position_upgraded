import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import * as path from "path";
import { exec } from "child_process";
import { promisify } from "util";
import crypto from "crypto";

const execAsync = promisify(exec);

export async function POST(req: NextRequest) {
  let testId = "";
  let dataPath = "";
  try {
    const formData = await req.formData();
    
    // Extract files from the form data
    const cmmFile = formData.get("cmm_data") as File | null;
    const sternumFile = formData.get("sternum_data") as File | null;
    const pressureFiles = formData.getAll("pressure_data") as File[];

    if (!cmmFile || !sternumFile || pressureFiles.length === 0) {
      return NextResponse.json(
        { error: "Missing required files." },
        { status: 400 }
      );
    }

    // Generate a unique test ID
    testId = crypto.randomUUID();
    
    // We will place the tmp directory inside the frontend folder, or OS tmpdir
    // path.join(process.cwd(), '.tmp') ensures it is within the project structure where it has write access
    dataPath = path.join(process.cwd(), ".tmp");
    const testDir = path.join(dataPath, testId);
    
    const excelDir = path.join(testDir, "DATA", "EXCEL");
    const frameDataDir = path.join(testDir, "DATA", "XSENSOR", "Rear", "Frame data");
    
    // Create necessary directories
    await fs.mkdir(excelDir, { recursive: true });
    await fs.mkdir(frameDataDir, { recursive: true });

    // Helper to write a File object to disk
    const writeStreamToFile = async (file: File, dest: string) => {
      const arrayBuffer = await file.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      await fs.writeFile(dest, buffer);
    };

    // Save Excel files to specific hardcoded expected names
    await writeStreamToFile(cmmFile, path.join(excelDir, "Left Rear Passenger.xlsx"));
    await writeStreamToFile(sternumFile, path.join(excelDir, "Chest deflection.xlsx"));

    // Save all pressure CSV files
    for (const pFile of pressureFiles) {
      if (pFile.name.endsWith(".csv")) {
        await writeStreamToFile(pFile, path.join(frameDataDir, pFile.name));
      }
    }

    // The current working directory is 'frontend'. The python project root is one level up.
    const projectRoot = path.join(process.cwd(), "..");
    
    // Run the python script
    // NOTE: using python3 as we are on macOS
    const command = `python3 -m src.belt_position.main --test-id "${testId}" --data-path "${dataPath}"`;
    
    try {
      const { stdout, stderr } = await execAsync(command, { cwd: projectRoot });
      console.log("Python stdout:", stdout);
      if (stderr) console.error("Python stderr:", stderr);
    } catch (e: unknown) {
      console.error("Python execution failed:", e);
      const errorMessage = e instanceof Error ? e.message : String(e);
      return NextResponse.json(
        { error: "Failed to process data. Ensure the python script is working correctly and all files are valid.", details: errorMessage },
        { status: 500 }
      );
    }

    // Read the output
    const outputFilePath = path.join(
      testDir,
      "DATA",
      "XSENSOR",
      "Rear",
      "Belt Position Debug",
      "interpolated_belt_chest_data.xlsx"
    );

    const fileBuffer = await fs.readFile(outputFilePath);

    // Clean up
    await fs.rm(testDir, { recursive: true, force: true });

    // Return the file
    return new NextResponse(fileBuffer, {
      status: 200,
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": 'attachment; filename="interpolated_belt_chest_data.xlsx"',
      },
    });

  } catch (err: unknown) {
      console.error("Error Processing:", err);
      // Cleanup on generic error
      if (dataPath && testId) {
        const testDir = path.join(dataPath, testId);
        await fs.rm(testDir, { recursive: true, force: true }).catch(() => {});
      }
      const errorMessage = err instanceof Error ? err.message : String(err);
      return NextResponse.json(
        { error: "An unexpected error occurred: " + errorMessage },
        { status: 500 }
      );
    }
}
