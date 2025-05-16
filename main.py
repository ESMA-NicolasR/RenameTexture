import sys
import shutil
from pathlib import Path

def main():
    folder = sys.argv[1]
    file_list = list_files(folder)
    print(file_list)
    output_dir = Path(folder) / "output"
    output_dir.mkdir(exist_ok=True)
    for p in file_list:
        basename = p.name.split("_M_")[0].split("SM_")[1]
        mapname = p.name.split(".png")[0].split("_")[-1]
        fullname = f"T_{mapname}_{basename}.png"
        rename_file(folder, p.name, output_dir, fullname)

def list_files(path):
    dir_path = Path(path)
    #return [file for file in dir_path.iterdir() if dir_path.glob("./.png")]
    return list(dir_path.glob("./*.png"))

def rename_file(og_folder, og_name, new_folder, new_name):
    og_path = Path(og_folder) / og_name
    new_path = Path(new_folder) / new_name
    #os.rename(og_path, new_path)
    shutil.copy(og_path, new_path)
    print(f"from {og_path} to {new_path}")


if __name__=="__main__":
    main()