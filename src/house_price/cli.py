"""Command-line interface used locally, by DVC, and inside Docker."""

import argparse
import json
from pathlib import Path

import pandas as pd

from house_price.config import load_config
from house_price.data import prepare_data
from house_price.predict import load_model, predict
from house_price.train import train_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="house-price")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-data", help="Unduh dataset bila belum tersedia.")
    prepare.add_argument("--output", default="data/raw/california_housing.csv")
    prepare.add_argument(
        "--from-source",
        action="store_true",
        help="Pulihkan dataset awal publik hanya jika checksum cocok dengan metadata DVC.",
    )
    train = commands.add_parser("train", help="Train, evaluasi, dan simpan pipeline ke MLflow.")
    train.add_argument("--data", default="data/raw/california_housing.csv")
    train.add_argument("--config", default="params.yaml")
    train.add_argument("--output", default="artifacts/training")
    train.add_argument("--tracking-uri")
    inference = commands.add_parser("predict", help="Prediksi dari CSV fitur mentah.")
    inference.add_argument("--model-uri", required=True)
    inference.add_argument("--input", required=True)
    inference.add_argument("--output", required=True)
    inference.add_argument("--tracking-uri")
    args = parser.parse_args(argv)
    if args.command == "prepare-data":
        print(prepare_data(args.output, from_source=args.from_source))
    elif args.command == "train":
        result = train_model(
            args.data,
            args.output,
            load_config(args.config),
            tracking_uri=args.tracking_uri,
        )
        print(json.dumps(result, indent=2))
    else:
        output = Path(args.output)
        if output.resolve() == Path(args.input).resolve() or output.exists():
            raise FileExistsError("Gunakan file output baru agar data yang ada tidak tertimpa.")
        model = load_model(args.model_uri, tracking_uri=args.tracking_uri)
        result = predict(model, pd.read_csv(args.input))
        output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output, index=False)
        print(output)
    return 0
