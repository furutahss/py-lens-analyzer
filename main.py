import os
import exifread
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor

logging.getLogger('exifread').setLevel(logging.ERROR)

# EXIFデータ取得
# @param    file_path 対象ファイルパス
# @returns  {ファイル名, レンズ名, 焦点距離, F値, シャッタースピード, ISO感度}
def get_exif_data(file_path):
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            # レンズ名
            lens_tag = tags.get('EXIF LensModel') or tags.get('Image LensModel') or "Unknown Lens"
            # 焦点距離
            focal_tag = tags.get('EXIF FocalLength')
            focal_length = 0
            if focal_tag:
                val = focal_tag.values[0]
                focal_length = float(val.num) / float(val.den) if hasattr(val, 'num') else float(val)
            # F値
            f_number_tag = tags.get('EXIF FNumber')
            f_number = 0.0
            if f_number_tag:
                val = f_number_tag.values[0]
                f_number = float(val.num) / float(val.den) if hasattr(val, 'num') else float(val)
            # シャッタースピード
            exposure_tag = tags.get('EXIF ExposureTime')
            exposure_time = "Unknown"
            exposure_val = 0.0
            if exposure_tag:
                exposure_time = str(exposure_tag)
                val = exposure_tag.values[0]
                exposure_val = float(val.num) / float(val.den) if hasattr(val, 'num') else float(val)
            # ISO感度
            iso_tag = tags.get('EXIF ISOSpeedRatings')
            iso = int(iso_tag.values[0]) if iso_tag else 0
            return {
                "FileName": file_path.name,
                "Lens": str(lens_tag),
                "FocalLength": focal_length,
                "FNumber": f_number,
                "ExposureTimeStr": exposure_time,
                "ExposureVal": exposure_val,
                "ISO": iso
            }
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

# メイン処理
# @returns  none
def main():
    parser = argparse.ArgumentParser(description="画像フォルダをスキャンしてレンズと焦点距離の統計を表示します")
    parser.add_argument("target_dir", type=str, help="解析対象のディレクトリパス")
    parser.add_argument("--output", "-o", type=str, default="outputs", help="結果の保存先フォルダ")    
    
    args = parser.parse_args()
    target_path = Path(args.target_dir)
    output_path = Path(args.output)

    if not target_path.exists():
        print(f"エラー: 指定されたディレクトリが見つかりません: {target_path}")
        return

    if not output_path.exists():
        output_path.mkdir(parents=True)

    image_extensions = {".jpg", ".jpeg", ".JPG", ".png", ".arw", ".ARW"}
    image_files = [f for f in target_path.glob("**/*") if f.suffix in image_extensions]

    if not image_files:
        print(f"画像ファイルが見つかりませんでした: {target_path}")
        return

    print(f"解析中... {len(image_files)} 枚の画像が見つかりました。")

    with ProcessPoolExecutor() as executor:
        results = list(executor.map(get_exif_data, image_files))

    data = [r for r in results if r is not None]
    df = pd.DataFrame(data)

    # グラフの作成と保存
    plt.figure(figsize=(10, 6))
    df['Lens'].value_counts().plot(kind='barh')
    plt.title('Lens Usage Statistics')
    plt.tight_layout()
    plt.savefig(output_path / 'lens_usage.png')

    plt.figure(figsize=(10, 6))
    df['FocalLength'].hist(bins=20, rwidth=0.9)
    plt.title('Focal Length Distribution')
    plt.tight_layout()
    plt.savefig(output_path / 'focal_distribution.png')

    plt.figure(figsize=(10, 6))
    df[df['FNumber'] > 0]['FNumber'].hist(bins=20, rwidth=0.9, color='orange')
    plt.title('Aperture (F-Number) Distribution')
    plt.savefig(output_path / 'aperture_distribution.png')

    plt.figure(figsize=(10, 6))
    df[df['ISO'] > 0]['ISO'].value_counts().sort_index().plot(kind='bar')
    plt.title('ISO Sensitivity Distribution')
    plt.savefig(output_path / 'iso_distribution.png')

    plt.figure(figsize=(10, 6))
    df['ExposureTimeStr'].value_counts().head(10).plot(kind='pie', autopct='%1.1f%%')
    plt.title('Shutter Speeds')
    plt.savefig(output_path / 'shutter_speed_pie.png')

    print(f"解析完了！ '{output_path}' フォルダに結果を保存しました。")

if __name__ == "__main__":
    main()
