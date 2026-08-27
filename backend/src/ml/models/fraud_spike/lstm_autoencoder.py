import numpy as np
import torch
import torch.nn as nn


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int = 1):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, input_dim, num_layers, batch_first=True)

    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        _, (hidden, _) = self.encoder(x)
        # hidden shape: (num_layers, batch, hidden_dim)

        # We use the last hidden state and repeat it for decoder
        hidden = hidden[-1].unsqueeze(1).repeat(1, x.size(1), 1)

        out, _ = self.decoder(hidden)
        return out

    def detect(self, sequence: np.ndarray, threshold: float) -> tuple[bool, float]:
        self.eval()
        with torch.no_grad():
            x = torch.FloatTensor(sequence).unsqueeze(0)  # add batch dim
            reconstructed = self(x)
            mse = torch.mean((x - reconstructed) ** 2).item()
            is_anomaly = mse > threshold
            return is_anomaly, mse

    def export_to_onnx(self, output_path: str, seq_len: int, input_dim: int):
        self.eval()
        dummy_input = torch.randn(1, seq_len, input_dim)
        torch.onnx.export(
            self,
            (dummy_input,),
            output_path,
            export_params=True,
            opset_version=12,
            do_constant_folding=True,
            input_names=["sequence_input"],
            output_names=["reconstructed"],
            dynamic_axes={"sequence_input": {0: "batch_size"}, "reconstructed": {0: "batch_size"}},
        )
