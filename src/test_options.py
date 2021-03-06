import multiprocessing
import argparse
import pprint
import sys

#=========1=========2=========3=========4=========5=========6=========7=

def load_arguments():
    argparser = argparse.ArgumentParser(sys.argv[0])

    argparser.add_argument('--cluster_struct',
            type=str,
            default='y')
    argparser.add_argument('--cluster_text',
            type=str,
            default='y')
    argparser.add_argument('--step',
            type=float,
            default=0.1)
    argparser.add_argument('--num_clusters',
            type=int,
            default=10)
    argparser.add_argument('--num_extensions',
            type=int,
            default=15)
    argparser.add_argument('--num_processes',
            type=int,
            default=multiprocessing.cpu_count()-1)
    argparser.add_argument('--dataset_path',
            type=str,
            default='')
    
    args = argparser.parse_args()

    print('------------------------------------------------')
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(vars(args))
    print('------------------------------------------------')

    return args
