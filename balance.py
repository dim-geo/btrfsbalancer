#!/usr/bin/python3

import btrfs
import sys
import time

def analyze_block_groups(fs):
    min_size=14000000000000000000
    min_size_block=None
    max_size=-1
    free_space=-1
    for chunk in fs.chunks():
        if not (chunk.type & btrfs.BLOCK_GROUP_DATA):
            continue
        try:
            block_group = fs.block_group(chunk.vaddr, chunk.length)
            #print(block_group)

            if block_group.used != 0 and block_group.used < min_size:
                if min_size_block != None:
                    free_space=min_size_block.length-min_size_block.used
                min_size=block_group.used
                print(min_size_block)
                min_size_block=block_group
            if block_group.used > max_size:
                max_size_size=block_group.used
        except IndexError:
            continue
    if min_size == max_size or min_size_block.used >= free_space:
        return None
    print(min_size_block,free_space)
    return min_size_block

def balance_block_group(fs,block_group):
    vaddr = block_group.vaddr
    args = btrfs.ioctl.BalanceArgs(vstart=block_group.vaddr, vend=block_group.vaddr+1)
    print("Balance block group vaddr {} used_pct {} ...".format(block_group.vaddr, block_group.used_pct), end='', flush=True)
    start_time = time.time()
    try:
        progress = btrfs.ioctl.balance_v2(fs.fd, data_args=args)
        end_time = time.time()
        print(" duration {} sec total {}".format(int(end_time - start_time), progress.considered))
    except KeyboardInterrupt:
        end_time = time.time()
        print(" duration {} sec".format(int(end_time - start_time)))
        raise

def main():
    number_of_blocks_to_balance = int(sys.argv[1])
    fs= btrfs.FileSystem(sys.argv[2])
    for i in range(0,number_of_blocks_to_balance):
            min_size_block = analyze_block_groups(fs)
            if min_size_block != None:
                balance_block_group(fs,min_size_block)
            else:
                break

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: {} <number_of_rebalance_blocks> <mountpoint>".format(sys.argv[0]))
        sys.exit(1)
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(130)  # 128 + SIGINT
    except Exception as e:
        print(e)
        sys.exit(1)
