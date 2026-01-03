import os
import exifread
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse

# EXIFデータ取得
# @param    file_path 対象ファイルパス
# @returns  {ファイル名, レンズ名, 焦点距離}
def get_exif_data(file_path):
    with open(file_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        lens_tag = tags.get('EXIF LensModel') or tags.get('Image LensModel') or "Unknown Lens"
        focal_tag = tags.get('EXIF FocalLength')
        focal_length = 0
        if focal_tag:
            try:
                val = focal_tag.values[0]
                focal_length = float(val.num) / float(val.den) if hasattr(val, 'num') else float(val)
            except:
                focal_length = 0
        return {"FileName": file_path.name, "Lens": str(lens_tag), "FocalLength": focal_length}

# メイン処理
# @returns  none
def main():
    parser = argparse.ArgumentParser(description="画像フォルダをスキャンしてレンズと焦点距離の統計を表示します")
    parser.add_argument(
        "target_dir", 
        type=str, 
        help="解析対象のディレクトリパスを指定してください"
    )
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        default="outputs", 
        help="結果の保存先フォルダ（デフォルト: outputs）"
    )
    
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

    data = []
    for img_path in image_files:
        try:
            info = get_exif_data(img_path)
            data.append(info)
        except Exception as e:
            print(f"Error reading {img_path}: {e}")

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

    print(f"解析完了！ '{output_path}' フォルダに結果を保存しました。")

if __name__ == "__main__":
    main()
