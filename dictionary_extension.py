

from matplotlib.pyplot import stem


original_dictionary_path = "idioms_extended.txt"
modified_dictionary_path = "idioms_extended_augmented.txt"

VERBS_ONLY = False
IGNORE_CUSTOM_DERIVATIONS = False

"""
Statistics from build as of 04/26/2022, 2:25pm
VERBS ONLY, NO CUSTOM
Precision: 0.19508523356209873
Recall: 0.5306515717210647

NOT VERBS ONLY, NO CUSTOM
Precision: 0.20031432420296363
Recall: 0.5372756834878959

VERBS ONLY, WITH CUSTOM
Precision: 0.14463613550815557
Recall: 0.5553414428519812
"""

# Use a Python Dictionary to store word groups and their modified forms
morphology_dictionary_path = "catvar_english_morphology.txt"
stem_derivations = {}
root = {}

# Load the morphological dictionary
print("Loading morphemes...")
for line in open(morphology_dictionary_path, "r"):
    line = line.strip().split()
    is_verb = line[2][1] == "V"
    if VERBS_ONLY and not is_verb:
        continue
    if line[1] not in stem_derivations:
        stem_derivations[line[1]] = []
    stem_derivations[line[1]].append(line[0])
    root[line[0]] = line[1]

additional_derivations_path = "custom_derivations.txt"
print("Loading custom derivations...")
if not IGNORE_CUSTOM_DERIVATIONS:
    for line in open(additional_derivations_path, "r"):
        line = line.strip().split() 
        if(len(line) < 2):
            continue
        while len(line) > 2:
            line[0] = line[0] + " " + line[1]
            line.pop(1)
        if line[1] not in stem_derivations:
            stem_derivations[line[1]] = []
        stem_derivations[line[1]].append(line[0])
        root[line[0]] = line[1]

INFLECTION_LIMIT = 8192

def recursive_search(words):
    if len(words) == 0:
        return [""]
    else:
        prev_result = recursive_search(words[1:])
        if words[0] not in root:
            root[words[0]] = words[0]
            stem_derivations[words[0]] = [words[0]]
        curr_root = root[words[0]] 
        result = []
        for word in prev_result:
            for derivation in stem_derivations[curr_root]:
                result.append(derivation + " " + word)
                if len(result) > INFLECTION_LIMIT:
                    return result
        return result
            


# Get file for outputing new dictionary
output_file = open(modified_dictionary_path, "w")


# Load the original dictionary
print("Beginning dictionary modification...")
current_line = 0
total_work = 0
for line in open(original_dictionary_path, "r"):
    line = line.strip().split()
    print("\rCurrent line: {}".format(current_line), end="")
    current_line += 1
    all_derivations = recursive_search(line)
    for derivation in all_derivations:
        derivation = derivation.replace("n't", " n't")
        derivation = derivation.replace("'ve", " 've")
        derivation = derivation.replace("'ll", " 'll")
        derivation = derivation.replace("'d", " 'd")
        derivation = derivation.replace("'s", " 's")
        derivation = derivation.replace("'re", " 're")
        derivation = derivation.replace("'m", " 'm")
        derivation = derivation.replace("'em", " 'em")
        derivation = derivation.replace("gonna", "gon na")
        derivation = derivation.replace("gotta", "got ta")
        total_work += len(derivation)
        output_file.write(derivation + "\n")

output_file.close()
print("\n" + str(total_work))

    
    


