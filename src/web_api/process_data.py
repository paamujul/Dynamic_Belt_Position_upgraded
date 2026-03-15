import os
from pathlib import Path

def extract_frame_by_time(master_csv_path: str, target_time: float, output_dir: str = "templates/DATA/XSENSOR"):
    master_path = Path(master_csv_path)
    out_dir = Path(output_dir)
    
    if not master_path.exists():
        raise FileNotFoundError(f"Master CSV not found at {master_csv_path}")
        
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "filtered_frame.csv"
    
    global_header = []
    current_block = []
    is_global_header = True
    found_target = False
    
    with open(master_path, 'r', encoding='latin1') as f:
        for line in f:
            clean_line = line.strip().replace('"', '')
            
            if clean_line.startswith("FRAME,"):
                if found_target:
                    # We have fully read the target block, stop reading
                    break
                is_global_header = False
                current_block = [line]
                continue
                
            if is_global_header:
                global_header.append(line)
            else:
                current_block.append(line)
                
                if clean_line.startswith("Time,"):
                    parts = clean_line.split(',')
                    if len(parts) > 1:
                        time_val = parts[1].strip()
                        try:
                            if abs(float(time_val) - float(target_time)) < 1e-5:
                                found_target = True
                                # Replace the Time line with Time,0
                                # Keep the original commas format
                                orig_parts = line.split(',')
                                orig_parts[1] = "0"
                                current_block[-1] = ','.join(orig_parts)
                        except ValueError:
                            pass
                            
    if not found_target:
        raise ValueError(f"Time frame {target_time} not found in the master CSV.")
        
    with open(out_file, 'w', encoding='latin1') as f:
        f.writelines(global_header)
        f.writelines(current_block)
        
    return str(out_file)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", required=True, help="Path to master CSV")
    parser.add_argument("--time", type=float, required=True, help="Target time string")
    parser.add_argument("--outdir", default="templates/DATA/XSENSOR", help="Output directory")
    args = parser.parse_args()
    
    try:
        out = extract_frame_by_time(args.master, args.time, args.outdir)
        print(f"Success! Extracted frame saved to: {out}")
    except Exception as e:
        print(f"Error: {e}")
