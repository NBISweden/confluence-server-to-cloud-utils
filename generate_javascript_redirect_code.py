import sys
import pdb

# define usage message
usage = f"Usage: python3 {sys.argv[0]} <input file name>"

# get input file name
try:
    input_filename = sys.argv[1]
except IndexError:
    print(usage)
    sys.exit()

# init
link_dict = {}

# for each line in the file
with open(input_filename, 'r') as file:
    for line in file:

        # remove newlines
        line = line.rstrip()
        
        # split line on whitespace
        parts = line.split('\t')

        # save the link
        link_dict[parts[0]] = parts[1]
        link_dict[parts[2]] = parts[1]  # map old short link to new full link
#        link_dict[parts[2]] = parts[3] # map old short link to new short link



# print the javascript code
print(f"const link_dict = new Map([")
for key in sorted(sorted(link_dict.keys()), key=len):
    print(f"    ['{key}', '{link_dict[key]}'],")
print(f"]);")




