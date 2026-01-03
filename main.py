import os
import exifread
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# EXIFデータ取得
# @param    file_path 対象ファイルパス
# @returns  {ファイル名, レンズ名, 焦点距離}
def get_exif_data(file_path):
    with open(file_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        
        # レンズ名の取得
        lens_tag = tags.get('EXIF LensModel') or tags.get('Image LensModel') or "Unknown Lens"
        
        # 焦点距離の取得
        focal_tag = tags.get('EXIF FocalLength')
        focal_length = 0
        if focal_tag:
            try:
                val = focal_tag.values[0]
                focal_length = float(val.num) / float(val.den) if hasattr(val, 'num') else float(val)
            except:
                focal_length = 0
                
        return {
            "FileName": file_path.name,
            "Lens": str(lens_tag),
            "FocalLength": focal_length
        }

# メイン処理
# @param    target_dir  対象フォルダ
# @returns  none
def main(target_dir):
    image_extensions = {".jpg", ".jpeg", ".JPG", ".png", ".arw", ".ARW"} # SonyのRAW(ARW)にも対応
    path = Path(target_dir)
    image_files = [f for f in path.glob("**/*") if f.suffix in image_extensions]

    print(f"解析中... {len(image_files)} 枚の画像が見つかりました。")

    data = []
    for img_path in image_files:
        try:
            info = get_exif_data(img_path)
            data.append(info)
        except Exception as e:
            print(f"Error reading {img_path}: {e}")

    # DataFrame化
    df = pd.DataFrame(data)

    if df.empty:
        print("有効なEXIFデータが見つかりませんでした。")
        return

    # 1. レンズ使用頻度の集計とグラフ化
    plt.figure(figsize=(10, 6))
    df['Lens'].value_counts().plot(kind='barh')
    plt.title('Lens Usage Statistics')
    plt.xlabel('Count')
    plt.tight_layout()
    plt.savefig('outputs/lens_usage.png')

    # 2. 焦点距離の分布
    plt.figure(figsize=(10, 6))
    df['FocalLength'].hist(bins=20, rwidth=0.9)
    plt.title('Focal Length Distribution')
    plt.xlabel('Focal Length (mm)')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('outputs/focal_distribution.png')

    print("解析完了！ outputs フォルダにグラフを保存しました。")

if __name__ == "__main__":
    target_path = '対象フォルダパス'
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
    main(target_path)
