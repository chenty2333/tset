import sys
import os
import string
from collections import OrderedDict

def main(args):
    csvfile = args[1]
    option = args[2]
    if option != "intra" or option != "only" or option != "inter" or option != "static":
        exit
    victim_to_polluter = {}
    vic_pol_to_cleaner = {}
    victim_to_info = {}
    with open(csvfile) as f:
        for line in f:
            slug = line.split(',')[0] # .split("https://github.com/")[1]
            sha = line.split(',')[1] # [0-7]
            module = line.split(',')[2]
            victim = line.split(',')[3]
            polluter = line.split(',')[4]
            cleaner = line.split(',')[5]
            test_type = line.split(',')[6].strip()

            # skip the first line with # 
            if victim == 'victim/brittle':
                continue
            
            slug = slug[19:]
            sha = sha[0:7]
            info_for_this_vic = []
            if not victim in victim_to_info:
                victim_to_info[victim] = [slug, sha, module, test_type]

            polluters_for_this_vic = set()
            if victim in victim_to_polluter:
                polluters_for_this_vic = victim_to_polluter[victim]
            if not polluter == "":
                polluters_for_this_vic.add(polluter)
            victim_to_polluter[victim] = polluters_for_this_vic
            
            cleaners_for_this_vp = set()
            if (victim, polluter) in vic_pol_to_cleaner:
                cleaners_for_this_vp = vic_pol_to_cleaner[(victim, polluter)]
            if "|" in cleaner:
                cleaner_for_this_victim = cleaner.split("|")
                for cftv in cleaner_for_this_victim:
                    if not cftv == "":
                        cleaners_for_this_vp.add(cftv)
            else:
                if not cleaner == "":
                    cleaners_for_this_vp.add(cleaner)
            vic_pol_to_cleaner[(victim, polluter)] = cleaners_for_this_vp
    
    # print(len(vic_pol_to_cleaner[("org.activiti.spring.boot.tasks.TaskRuntimeTaskForOtherTest.aCreateStandaloneTaskWithNoCandidates", "org.activiti.spring.boot.tasks.TaskRuntimeTaskAssigneeTest.aCreateStandaloneTaskForAnotherAssignee")]))


    # for victim, this means we can find the failing order
    victim_to_found = {}
    # for victim, it means the index of the failing order
    victim_to_order = {}

    # for victim, this means we can find the passing order
    victim_pass = {}
    # for victim, this means the index of the passing order
    victim_pass_order = {}

    for v in victim_to_polluter.keys():
        victim_to_found[v] = False
        victim_to_order[v] = 0
        victim_pass[v] = False
        victim_pass_order[v] = 0

    modula_key = ""
    for v in victim_to_polluter.keys():
        if victim_to_found[v] == True:
            continue
        if victim_pass[v] == True:
            continue
        
        cur_slug = victim_to_info[v][0]
        cur_sha = victim_to_info[v][1]
        cur_mod = victim_to_info[v][2]
        cur_type = victim_to_info[v][3]
        
        cur_slug = cur_slug.replace("/", "_") 
        cur_mod = cur_mod.replace("./", "").replace("/", "_")
        if option == "intra":
            dirname = sys.path[0] + "/../../orders/intra-orders/" + cur_slug + "-" + cur_mod + "-" + cur_sha + "-intra-orders/"
        elif option == "only":
            dirname = sys.path[0] + "/../../orders/only-orders/" + cur_slug + "-" + cur_mod + "-" + cur_sha + "-only-orders/"
        elif option == "inter":
            dirname = sys.path[0] + "/../../orders/inter-orders/" + cur_slug + "-" + cur_mod + "-" + cur_sha + "-inter-orders/"
        elif option == "static":
            dirname = sys.path[0] + "/../../orders/static-orders/" + cur_slug + "-" + cur_mod + "-" + cur_sha + "-static-orders/"
        
        if not os.path.exists(dirname):
            continue
        num_of_orders = len([name for name in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, name))])

        # get the original order
        original_order = []
        oo_file = sys.path[0] + "/../../data/original-orders/" + cur_slug + "-" + cur_mod + "-" + cur_sha + "-original_order"
        foo = open(oo_file, "r")
        loo = foo.readline()
        while loo:
            original_order.append(loo.strip())
            loo = foo.readline()
        foo.close()
        orders = []
        if int(num_of_orders) > 0:
            orders_dir = dirname
            for i in range(num_of_orders):

                # no this order, skip that order
                order_file = orders_dir + "order-" + str(i)
                order = []
                if not os.path.exists(order_file):
                    continue
                
                # obtain the order
                fi = open(order_file, "r")
                li = fi.readline()
                while li:
                    if li.strip().isdigit():
                        c = int(li)
                        order.append(original_order[c])
                    else:
                        order.append(li.strip())
                    li = fi.readline()
                fi.close()
                orders.append(order)

                # no this victim in this order, skip
                if not v in order:
                    continue

                index = order.index(v)
                
                # only need to process the polluters in this order
                polluters = victim_to_polluter[v]
                polluters_in_order = set()
                for polluter_item in polluters:
                    if polluter_item in order:
                        polluters_in_order.add(polluter_item)

                polluter_indice = []
                for p in polluters_in_order:
                    index_p = order.index(p)
                    polluter_indice.append(index_p)

                before_polluter_indice = []
                for ip in polluter_indice:
                    if ip >= index:
                        continue
                    else:
                        before_polluter_indice.append(ip)

                if len(before_polluter_indice) > 0:
                    # if it is a brittle, this can pass definitely
                    if victim_to_info[v][3] == "brittle":
                        if victim_pass[v] == False:
                            victim_pass[v] = True
                            victim_pass_order[v] = i
                        continue # still need to check the other orders - if this brittle can fail
                    
                    count = 0
                    for index_po in before_polluter_indice:
                        this_p = order[index_po]

                        cleaners_for_this_vp = vic_pol_to_cleaner[(v, this_p)]
                        cleaners_in_this_order = []
                        for c in cleaners_for_this_vp:
                            if c in order:
                                cleaners_in_this_order.append(c)
                        
                        cleaner_indice = []
                        for c in cleaners_in_this_order:
                            index_c = order.index(c)
                            cleaner_indice.append(index_c)
                        
                        largest_index_c = -1
                        for ic in cleaner_indice:
                            if ic >= index:
                                continue
                            else:
                                if ic > largest_index_c:
                                    largest_index_c = ic
                        
                        if largest_index_c >= 0:
                            if largest_index_c > index_po:
                                count += 1
                                if victim_pass[v] == False and count == len(before_polluter_indice):
                                    victim_pass[v] = True
                                    victim_pass_order[v] = i
                                    break
                            else:
                                if victim_to_found[v] == False:
                                    victim_to_found[v] = True
                                    victim_to_order[v] = i
                                break
                        else:
                            if victim_to_found[v] == False:
                                victim_to_found[v] = True
                                victim_to_order[v] = i
                            break
                else:
                    if victim_to_info[v][3] == "brittle":
                        if victim_to_found[v] == False:
                            victim_to_found[v] = True
                            victim_to_order[v] = i
                        # continue
                    else:
                        if victim_pass[v] == False:
                            victim_pass[v] = True
                            victim_pass_order[v] = i
                        # continue
                if victim_pass[v] == True and victim_to_found[v] == True:
                    break             
    
    for v in victim_to_found.keys():
        print(victim_to_info[v][0] + "," + victim_to_info[v][1] + "," + victim_to_info[v][2] + "," + v + "," + str(victim_pass[v]) + "," + str(victim_pass_order[v]) + "," + str(victim_to_found[v]) + "," + str(victim_to_order[v]))
    
if __name__ == '__main__':
    main(sys.argv)
