#!/usr/bin/env python

import argparse
from reporting.dataset_reporter import DatasetReporter


def get_cli_arguments():
    parser = argparse.ArgumentParser(description='Reports on topic-modeling datasets', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--details', '-d', dest='details', default=False, action='store_true', help='Switch to show details about the datasets')
    parser.add_argument('--select-dataset', '-s', dest='dataset_label', help='Whether to show information about a specific dataset only.')
    return parser.parse_args()


if __name__ == '__main__':
    cols_root_dir = '/data/thesis/data/collections'
    args = get_cli_arguments()
    dt_rprt = DatasetReporter(cols_root_dir)

    multiline_datasets_strings = dt_rprt.get_infos(details=args.details, selection=args.dataset_label)

    if args.dataset_label:
        l = []
        for i, line in enumerate(multiline_datasets_strings):
            if args.dataset_label in line:
                print(line)
                break
                # l.extend([line] + multiline_datasets_strings[i + 1 : i + 5])
                # break
        # print('\n'.join(l))
    # b = '\n'.join(dt_rprt.get_infos(details=args.details))
    else:
        print('\n'.join(multiline_datasets_strings))
