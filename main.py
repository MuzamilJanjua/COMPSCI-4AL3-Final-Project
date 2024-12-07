import pandas as pd
from torch.utils.data import DataLoader, random_split
import torch.nn as nn
import torch
import numpy as np

import feature_handlers as fh
import model_lib as ml


def main(parent_dir: str, src_file: str) -> None:
    torch.manual_seed(42)
    np.random.seed(42)
    print("Torch CUDA available:", torch.cuda.is_available())
    # parsed_file_name = f"parsed_{src_file}"
    # feature_file_name = f"features_{src_file}"
    # parsed_path = f"{parent_dir}/{parsed_file_name}"
    # feature_path = f"{parent_dir}/{feature_file_name}".replace(".pgn", ".pkl")

    # game_data = []
    # for game in fh.iterate_games(parsed_path):
    #     game_header_values, game_moves = fh.pgn_game_to_data(game)
    #     game_data.append([*game_header_values, game_moves])

    # games = pd.DataFrame(game_data, columns=[fh.HEADERS_TO_KEEP, "Moves"])
    # games.to_pickle(feature_path)
    # Load the data for training and testing

    temp_test_path = f"Data/2024-08/xaa.pgn"
    game_data = fh.pgn_file_to_dataframe(temp_test_path)
    game_dataset = ml.ChessDataset(game_data, 10)

    # print(len(game_dataset[0]))
    # print(game_dataset[0][0].dtype)
    # print(game_dataset[0][1].dtype)
    # print(game_dataset[0][2].dtype)
    # print(game_dataset[0][3].dtype)

    # train_set = load_mnist(parent_path, "train")
    # test_set = load_mnist(parent_path, "t10k")

    # Split the train set so we have a held-out validation set
    # Split the dataset into training (80%) and testing (20%)
    print(len(game_dataset))
    test_size = int(0.2 * len(game_dataset))
    train_size = len(game_dataset) - test_size
    train_data, test_data = random_split(game_dataset, [train_size, test_size], generator=torch.Generator().manual_seed(42))
    # print(test_data[0][1].shape)
    # Define the validation size as 20% of the training data
    validation_size = int(0.2 * train_size)
    train_size_split = train_size - validation_size  # Remaining size for training

    # Split the training data into training and validation sets
    train_set_split, validation_set_split = random_split(train_data, [train_size_split, validation_size], generator=torch.Generator().manual_seed(42))

    # Initialize the model and move it to the GPU if available
    model = ml.ChessNN()
    model.to(ml.device)

    # Initialize the data loaders, using a batch size of 128
    batch_size = 32
    train_loader = DataLoader(train_set_split, batch_size=batch_size, collate_fn=ml.collate_fn)
    validation_loader = DataLoader(validation_set_split, batch_size=batch_size, collate_fn=ml.collate_fn)
    test_loader = DataLoader(test_data, batch_size=batch_size, collate_fn=ml.collate_fn)

    # Calculate class weights
    class_counts = torch.bincount(torch.tensor([int(label) for label in game_dataset.labels[train_set_split.indices]]))
    class_weights = 1.0 / class_counts
    class_weights = class_weights / class_weights.sum()
    class_weights = class_weights.to(ml.device)

    # Use weighted loss
    loss_function = nn.CrossEntropyLoss(weight=class_weights)

    # Train the model
    train_losses, validation_losses, train_accuracy, validation_accuracy = ml.train(
        model,
        loss_function=loss_function,
        train_loader=train_loader,
        test_loader=validation_loader,
        print_every=2,
        learning_rate=0.005,
        epoch=200,
    )

    ml.plot_eval_results(train_losses, validation_losses)
    ml.plot_eval_results(train_accuracy, validation_accuracy)
    # Kind of a hack, but limit all datasets (including the test set) to 20 moves
    # can be changed multiple times and will change the resulting test loader
    print("MOVE LIMIT 1")
    game_dataset.move_limit = 1
    ml.printPerformaceMetrics(model=model, test_loader=test_loader)
    print("MOVE LIMIT 5")
    game_dataset.move_limit = 5
    ml.printPerformaceMetrics(model=model, test_loader=test_loader)
    print("MOVE LIMIT 10")
    game_dataset.move_limit = 10
    ml.printPerformaceMetrics(model=model, test_loader=test_loader)
    print("20 MOVE LIMIT")
    game_dataset.move_limit = 20
    ml.printPerformaceMetrics(model=model, test_loader=test_loader)
    print("NO MOVE LIMIT")
    game_dataset.move_limit = None
    ml.printPerformaceMetrics(model=model, test_loader=test_loader)
    # TODO get accuracy on all move limits from 1 to 100


if __name__ == "__main__":
    parent_dir = "OriginalData"
    src_file = "lichess_db_standard_rated_2024-10.pgn"
    main(parent_dir, src_file)
