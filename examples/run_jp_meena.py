import argparse
import random

import numpy as np
import torch

import sentencepiece as spm
from dialogue_generation_models.configuration_meena import MeenaConfig
from dialogue_generation_models.modeling_meena import MeenaForConditionalGeneration


parser = argparse.ArgumentParser()
parser.add_argument(
    "--pretrained-model-path",
    default="/nas/models/jp_meena/torch_weights/base_filter.pth",
    type=str,
    help="Path to pre-trained model",
)
parser.add_argument(
    "--model-config-path",
    default="./configs/base_meena_config.json",
    type=str,
    help="Path to model configuration file",
)
parser.add_argument(
    "--tokenizer-model-path",
    default="./tokenizer/jp_spm.model",
    type=str,
    help="Path to Sentencepiece model",
)
parser.add_argument(
    "--decoding-method",
    default="beam_search",
    type=str,
    help="Decoding method (beam_search or top_p)",
)


def main(args):
    np.random.seed(42)
    torch.manual_seed(42)
    random.seed(42)
    tokenizer = spm.SentencePieceProcessor(model_file=args.tokenizer_model_path)

    config = MeenaConfig.from_json(args.model_config_path)
    model = MeenaForConditionalGeneration(config)
    model.load_state_dict(torch.load(args.pretrained_model_path, map_location="cpu"))
    model.eval()

    contexts = [
        ["どこ住んでるの?"],
        ["どこ住んでるの?", "長久手!"],
        ["どこ住んでるの?", "長久手!", "いいところ住んでるじゃん"],
        ["どこ住んでるの?", "長久手!", "いいところ住んでるじゃん", "wwでも駅からかなり遠いよ"],
        ["どこ住んでるの?", "長久手!", "いいところ住んでるじゃん", "wwでも駅からかなり遠いよ", "確かに!駅から遠いとね、、、"],
    ]

    for context in contexts:
        # insert [SEPT] between input utterances
        input_id = [
            token_id
            for raw_str in context
            for token_id in tokenizer.encode(raw_str, out_type=int) + [config.sept_token_id]
        ] + [config.bos_token_id]

        input_tensor = torch.tensor([input_id])

        if args.decoding_method == "top_p":
            outputs = model.generate(
                input_ids=input_tensor,
                max_length=256,
                min_length=8,
                temperature=1.0,
                do_sample=True,
                top_p=0.8,
                pad_token_id=config.pad_token_id,
                bos_token_id=config.bos_token_id,
                eos_token_id=config.eos_token_id,
                repetition_penalty=1.3,
                no_repeat_ngram_size=3,
                num_return_sequences=10,
            )
        elif args.decoding_method == "beam_search":
            outputs = model.generate(
                input_ids=input_tensor,
                max_length=256,
                min_length=8,
                num_beams=10,
                pad_token_id=config.pad_token_id,
                bos_token_id=config.bos_token_id,
                eos_token_id=config.eos_token_id,
                repetition_penalty=1.3,
                no_repeat_ngram_size=3,
                num_return_sequences=5,
            )
        else:
            raise ValueError("Enter the right decoding method (top_p or beam_search)")

        context_str = " [SEPT] ".join(context)
        for output in outputs.tolist():
            decoded_response = tokenizer.decode(output)
            print(f"Context: {context_str} \t Reply: {decoded_response}")


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
