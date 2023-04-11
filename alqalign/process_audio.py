from allosaurus.audio import read_audio, write_audio, split_audio, silent_audio, concatenate_audio, Audio
import numpy as np
from pathlib import Path
from tqdm import tqdm
from alqalign.config import logger
from alqalign.model import read_am
import datetime
import kaldiio
import torch
from alqalign.utils import read_audio_rspecifier


def transcribe_audio(audio_file, lang_id, data_dir, duration=15.0, batch_size=8, verbose=False):

    if (data_dir / f'logit.npz').exists():
        return

    data_dir.mkdir(parents=True, exist_ok=True)

    audio = read_audio_rspecifier(audio_file)

    logger.info(f"total audio duration: {audio.duration()}")

    audio_lst = split_audio(audio, duration=duration)

    am = read_am(lang_id)

    logits, decode_info_lst = am.get_logits_batch(audio_lst, lang_id, batch_size=batch_size)

    logit_lst = []

    for logit in logits:
      lpz = logit[1]
      lpz = np.concatenate([lpz, lpz[-1][np.newaxis, :]], axis=0)
      logit_lst.append(lpz)

    lpz = np.concatenate(logit_lst, axis=0)

    lpz.dump(data_dir / f'logit.npz')

    w = open(data_dir / f'decoded.txt', 'w')

    #print(decode_info_lst)

    for i, token_pair in enumerate(decode_info_lst):
        utt_id = token_pair[0]
        decoded_info = token_pair[1]

        assert int(utt_id) == i

        chunk_start_time = i*duration
        # chunk_end_time = str(datetime.timedelta(seconds=(i+1)*duration))

        for phone_info in decoded_info:
            start_time = phone_info['start'] + chunk_start_time
            duration = phone_info['duration']
            phone = phone_info['phone']
            prob = phone_info['prob']

            w.write(f"{utt_id} {start_time:.3f} {duration:.3f} {phone} {prob}\n")

    w.close()


    # if am is None:
    #     am = read_recognizer('xlsr_transformer', '/home/xinjianl/Git/asr2k/data/model/031901/model_0.231203.pt', 'phone', 'raw')
    #
    # for file in tqdm(sorted(audio_dir.glob('*.wav'))):
    #     name = file.stem
    #     print('transcribing audio ', file)
    #     res = am.get_logits(file, lang_id)
    #     lpz = res[0][0].cpu().detach().numpy()
    #     lpz = np.concatenate([lpz, lpz[-1][np.newaxis, :]], axis=0)
    #     lpz.dump(logit_dir / f'{name}.npz')