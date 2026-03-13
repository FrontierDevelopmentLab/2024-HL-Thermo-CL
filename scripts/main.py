# from train_time_series_karman import train as train_tft
# from train_base_karman import train as train_base
import sys
import time
import os

if __name__ == "__main__":
    time_start = time.time()

    # parser = argparse.ArgumentParser(description='HL-24 Karman Model Training', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument('--model', type=str, default='base', help='Model family script to call')
    # opt = parser.parse_args()

    if 'MODEL' not in os.environ:
        raise RuntimeError("Environment variable MODEL must be defined.")

    match os.environ['MODEL']:
        case "tft":
            # train_tft()
            pass
        case "base":
            # train_base()
            pass
        case _:
            raise NotImplementedError("Selected model is not implemented.")
        
    print('\nTotal duration: {}'.format(time.time() - time_start))
    sys.exit(0)

