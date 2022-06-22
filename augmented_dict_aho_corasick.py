from xml.etree.ElementInclude import include
import jsonlines
import string
import ahocorasick as ac

dictionary_path = "idioms_extended_augmented.txt"
corupus_path = "magpie_unfiltered.jsonl"
#corupus_path = "magpie_test_data.jsonl"

A = ac.Automaton()


# Load dictionary
idx = 0
with open(dictionary_path, "r") as f:
    for line in f:
        x = line.strip()
        A.add_word(x, (idx, x))
        idx += 1

A.make_automaton()


def process(context):
    context = context.lower()
    res = ""
    indices = []
    ptr = 0
    for x in context:
        if x in string.ascii_letters or x in string.digits or x == "\'":
            res += x
            indices.append(ptr)
        elif x in string.whitespace and (len(res) == 0 or res[-1] not in string.whitespace):
            res += " "
            indices.append(ptr)
        ptr += 1

    return res, indices

# Load corpus
instances = 0
total_identified = 0
accurately_identified = 0
curr = 0
print("Running tests\n")
with jsonlines.open(corupus_path) as reader:
    for instance in reader:
        curr += 1
        print("\r{}".format(curr), end="")
        if instance["confidence"] == 1.0:
            instances += 1
            idiom_begin = instance["offsets"][0][0]
            idiom_end = instance["offsets"][-1][1] - 1
            context_list = instance["context"]

            # keep set of used start indices, to ensure only one match is found for each candidate
            used_start_indices = {}

            # Aho-Corasick is rediculously fast

            found_match = False

            for context in context_list:
                orig_context = context
                curr_idiom_end = idiom_end
                while curr_idiom_end < len(context) and curr_idiom_end >= 0 and context[curr_idiom_end] not in string.ascii_letters:
                    curr_idiom_end -= 1
                context, indices = process(context)
                for end_index, (insert_order, original_value) in A.iter(context):
                    start_index = end_index - len(original_value) + 1
                    if start_index not in used_start_indices:
                        used_start_indices[start_index] = end_index
                        total_identified += 1
                    elif end_index > used_start_indices[start_index]:
                        used_start_indices[start_index] = end_index
                        #In the final version, where we need to return the actual indices, we can defer to the longest match

                    if idiom_begin == indices[start_index] and curr_idiom_end == indices[end_index]:
                        accurately_identified += 1
                        found_match = True
        
      

print("")
print(str(accurately_identified) + " " + str(total_identified))
        

print("")
print("Precision: " + str(accurately_identified/total_identified))
print("Recall: " + str(accurately_identified/instances))
