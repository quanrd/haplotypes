"""
pull out haplotypes overlapping a region
write haplotype lengths for pairs of individuals within that region vs 
"""
import argparse
import gzip
from collections import defaultdict
import re
from datetime import datetime


def current_time():
    return(' [' + datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + ']')


def open_file(filename):
    if filename.endswith('gz'):
        my_file = gzip.open(filename)
    else:
        my_file = open(filename)
    return my_file


def header_dict(my_header):
    header = dict(zip(my_header, range(len(my_header))))
    return(header)


def main(args):
    # read all ind info
    ind_info = open_file(args.ind_info)
    header = ind_info.readline().strip().split(',')
    header = header_dict(header)
    geno_exome = {}
    for line in ind_info:
        line = line.strip().split(',')
        geno_exome[line[header['ID2']]] = line[header['exome_id']]
    exomes_intersect = set(geno_exome.values())

    # read vcf info
    vcf = open_file(args.vcf)
    vcf_dict = defaultdict(dict)  # pos -> ind -> geno
    snp_count = defaultdict(dict)  # pos -> geno -> ind
    snp_order = []  # store order to print snps in
    chr_snps = {}  # only go through each chromosome haps once
    vcf_inds = set()  # this lists everyone in the VCF
    header_order = []
    print 'Reading VCF' + current_time()
    for line in vcf:
        line = line.strip().split('\t')
        if line[0].startswith('##'):
            pass
        elif line[0].startswith('#CHROM'):
            vcf_header = header_dict(line)
            for i in line:
                i = re.sub(' ', '_', i)  # deal with fucking spaces in IDs
                vcf_inds.add(i)
                header_order.append(i)
        else:
            snp_id = '_'.join([line[vcf_header['#CHROM']], line[vcf_header['POS']], line[vcf_header['REF']], line[vcf_header['ALT']]])
            snp_order.append(snp_id)
            if line[vcf_header['#CHROM']] in chr_snps:
                chr_snps[line[vcf_header['#CHROM']]].append([line[vcf_header['POS']], line[vcf_header['REF']], line[vcf_header['ALT']]])
            else:
                chr_snps[line[vcf_header['#CHROM']]] = [[line[vcf_header['POS']], line[vcf_header['REF']], line[vcf_header['ALT']]]]
            [int(line[vcf_header['POS']]), line[vcf_header['REF']], line[vcf_header['ALT']]]
            for ind in range(9, len(header_order)):
                # store genotypes for every pos and individual
                vcf_dict[snp_id][header_order[ind]] = line[ind].split(':')[0]
                if snp_id in snp_count and line[ind].split(':')[0] in snp_count[snp_id] and header_order[ind] in exomes_intersect:
                    snp_count[snp_id][line[ind].split(':')[0]].append(header_order[ind])
                elif header_order[ind] in exomes_intersect:
                    snp_count[snp_id][line[ind].split(':')[0]] = [header_order[ind]]
            print snp_count[snp_id].keys()
            for geno in snp_count[snp_id].keys():
                print len(snp_count[snp_id][geno])

    # read all haplotype info
    snp_tot = defaultdict(dict)  # pos -> geno -> sorted pairs
    snp_num = defaultdict(dict)  # pos -> geno -> num pairs
    snp_len = defaultdict(dict)  # pos -> geno -> lengths list
    print chr_snps
    for chrom in chr_snps:
        haps = open_file(re.sub(r'chr\d+', 'chr' + chrom, args.haps))
        count = 0
        for line in haps:
            if not count % 1000000:
                print str(count) + current_time()
            count += 1
            line = line.strip().split()
            ind1 = line[1].split('.')[0]
            ind2 = line[3].split('.')[0]
            if geno_exome[ind1] in vcf_inds and geno_exome[ind2] in vcf_inds:
                ind1 = geno_exome[ind1]  # convert IDs, ADDED
                ind2 = geno_exome[ind2]  # convert IDs, ADDED
                for pos in chr_snps[chrom]:
                    snp_id = chrom + '_' + '_'.join(map(str, pos))
                    if int(pos[0]) >= int(line[5]) and int(pos[0]) <= int(line[6]):
                        # need to check if inds share snp
                        if vcf_dict[snp_id][ind1] == vcf_dict[snp_id][ind2]:
                            if snp_id in snp_num and vcf_dict[snp_id][ind1] in snp_num[snp_id]:
                                snp_num[snp_id][vcf_dict[snp_id][ind1]].add(tuple(sorted([ind1, ind2]))) ##+= 1 ##
                                snp_len[snp_id][vcf_dict[snp_id][ind1]].append(line[10])
                            else:
                                snp_num[snp_id][vcf_dict[snp_id][ind1]] = set(tuple(sorted([ind1, ind2]))) ##1
                                snp_len[snp_id][vcf_dict[snp_id][ind1]] = [line[10]]
                    ###NOTE: this won't work in non-Finns where it's not guaranteed that some individuals won't share haplotypes
                    if vcf_dict[snp_id][ind1] == vcf_dict[snp_id][ind2]:
                        if snp_id in snp_tot and vcf_dict[snp_id][ind1] in snp_tot[snp_id]:
                            snp_tot[snp_id][vcf_dict[snp_id][ind1]].add(tuple(sorted([ind1, ind2]))) #these can be the same ind
                        else:
                            snp_tot[snp_id][vcf_dict[snp_id][ind1]] = set(tuple(sorted([ind1, ind2]))) #these can be the same ind
                        # except KeyError:
                        #     print snp_id
                        #     print vcf_dict[snp_id].keys()
                        #     print vcf_dict.keys()
                        #     break

    out = gzip.open(args.out, 'w')
    out.write('\t'.join(['chr', 'pos', 'ref', 'alt', 'r_tot', 'h_tot', 'a_tot', 'rr_tot', 'hh_tot', 'aa_tot', 'rr_haps', 'hh_haps', 'aa_haps', 'rr_len', 'hh_len', 'aa_len']) + '\n')
    possible_genos = ['0/0', '0/1', '1/1']
    for snp in snp_order:
        out.write('\t'.join(snp.split('_')) + '\t')
        print snp_tot[snp].keys()
        print snp_num[snp].keys()
        print snp_len[snp].keys()
        #print snp_num
        for geno in possible_genos:
            if geno in snp_count[snp]:
                out.write(str(len(snp_count[snp][geno])) + '\t')
            else:
                out.write('0\t')
        for geno in possible_genos:
            if geno in snp_tot[snp]:
                out.write(str(len(snp_tot[snp][geno])) + '\t')
            else:
                out.write('0\t')
        for geno in possible_genos:
            if geno in snp_num[snp]:
                out.write(str(len(snp_num[snp][geno])) + '\t')
            else:
                out.write('0\t')
        for geno in possible_genos:
            if geno in snp_len[snp]:
                out.write(','.join(snp_len[snp][geno]) + '\t')
            else:
                out.write('NA\t')
        out.write('\n')
    # print overlapping inds present
    # print number of pairwise haps shared between inds
    # print new inds present

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse some args')
    parser.add_argument('--haps')
    parser.add_argument('--ind_info')
    parser.add_argument('--vcf')
    parser.add_argument('--out')
    
    args = parser.parse_args()
    main(args)
