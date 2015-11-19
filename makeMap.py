__author__ = 'armartin'
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Parse some args')
    parser.add_argument('--chr', default='22') #will replace chr[\d] with chr[chr]
    parser.add_argument('--genmap')
    parser.add_argument('--bim')
    parser.add_argument('--map_bim', default='bim') #read/write map/bim files
    parser.add_argument('--out')
    
    args = parser.parse_args()
    
    genmap = open(args.genmap)
    genmap.readline()
    #position COMBINED_rate(cM/Mb) Genetic_Map(cM)
    #72765 0.1245577896 0
    start = genmap.readline().strip().split()
    (start_bp, start_cM) = (start[0], start[2])
    end = genmap.readline().strip().split()
    (end_bp, end_cM) = (end[0], end[2])
    
    bim = open(args.bim)
    if args.out is not None:
        my_map = open(args.out, 'w')
    else:
        my_map = open(args.bim.replace('bim', 'map'), 'w')
    
    bim_line = bim.readline().strip().split()
    chr = args.chr
    print chr
    
    (rsid, phys_pos, a0, a1) = (bim_line[1], bim_line[3], bim_line[4], bim_line[5])
    while phys_pos < start_bp:
        proportion = (float(phys_pos) * float(start_cM)) / float(start_bp)
        write_map(my_map, [chr, rsid, str(proportion), phys_pos, a0, a1])
        bim_line = bim.readline().strip().split()
        (rsid, phys_pos, a0, a1) = (bim_line[1], bim_line[3], bim_line[4], bim_line[5])

    current_args = [phys_pos, start_bp, end_bp, rsid, bim, start_cM, end_cM, genmap, my_map, args.chr, a0, a1]
    current_args = check_conditions(*current_args)
    
    for bim_line in bim:
        bim_line = bim_line.strip().split()
        (rsid, phys_pos, a0, a1) = (bim_line[1], bim_line[3], bim_line[4], bim_line[5])
        try:
            (current_args[0], current_args[3], current_args[10], current_args[11]) = (phys_pos, rsid, a0, a1)
        except TypeError:
            print current_args
            print [phys_pos, rsid, a0, a1]
        current_args = check_conditions(*current_args)
    
    my_map.close()

#don't start genetic positions quite at 0 because this throws off program (e.g. hapi-ur) assumptions
def write_map(my_map, write_vars):
    write_vars[2] = str(write_vars[2])
    if str(write_vars[2]) == '0.0':
        write_vars[2] = 1e-4
    my_map.write('\t'.join(map(str, write_vars)) + '\n')

def check_conditions(phys_pos, start_bp, end_bp, rsid, bim, start_cM, end_cM, genmap, my_map, chr, a0, a1):
    my_var = True
    my_map.flush()
    while my_var:
        if int(phys_pos) > int(end_bp):
            #Criteria 1 - genotypes ahead of genetic map
            while int(phys_pos) > int(end_bp):
                (start_bp, start_cM) = (end_bp, end_cM)
                end = genmap.readline().strip().split() 
                if end == []:
                    proportion = (float(phys_pos) * float(end_cM)) / float(end_bp)
                    write_map(my_map, [chr, rsid, str(proportion), phys_pos, a0, a1])
                    my_var = False
                    return [phys_pos, start_bp, end_bp, rsid, bim, start_cM, end_cM, genmap, my_map, chr, a0, a1]
                else:
                    (end_bp, end_cM) = (end[0], end[2])
        else:
            #Criteria 2 - genotypes not ahead of genetic map
            if phys_pos == start_bp:
                write_map(my_map, [chr, rsid, str(start_cM), phys_pos, a0, a1])
                return [phys_pos, start_bp, end_bp, rsid, bim, start_cM, end_cM, genmap, my_map, chr, a0, a1]
            elif phys_pos == end_bp:
                write_map(my_map, [chr, rsid, str(end_cM), phys_pos, a0, a1])
                return [phys_pos, start_bp, end_bp, rsid, bim, start_cM, end_cM, genmap, my_map, chr, a0, a1]
            elif int(phys_pos) > int(start_bp) and int(phys_pos) < int(end_bp):
                interpolate = float((int(phys_pos) - int(start_bp))*(float(end_cM) - float(start_cM)))/(int(end_bp) - int(start_bp)) + float(start_cM)
                write_map(my_map, [chr, rsid, str(interpolate), phys_pos, a0, a1])
                return [phys_pos, start_bp, end_bp, rsid, bim, start_cM, end_cM, genmap, my_map, chr, a0, a1]
            else:
                print 'Criteria 2 - Something wrong when genetic data is before physical positions'
            break
            
if __name__ == '__main__':
    main()