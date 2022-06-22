from math import factorial
import jsonlines

dictionary_path = "idioms_wiktionary.txt"
corupus_path = "magpie_unfiltered.jsonl"

# Load dictionary
idiom_dictionary = set()
total_expected_work = 0
with open(dictionary_path, "r") as f:
    for line in f:
        x = line.strip()
        idiom_dictionary.add(x)
        #count spaces in remaining word
        spaces = x.count(" ")


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
            # This can be made a lot faster with a Trie
            # Or Aho-Corasick would be even better
            # But this is reasonably fast for now
            for context in context_list:
                context = context.lower()
                for i in range(len(context)):
                    for j in range(i+1, len(context)):
                        if idiom_dictionary.__contains__(context[i:j+1]):
                            total_identified += 1
                            if idiom_begin == i and idiom_end == j:
                                accurately_identified += 1

print("")
print(str(accurately_identified) + " " + str(total_identified))
        

print("")
print("Precision: " + str(accurately_identified/total_identified))
print("Recall: " + str(accurately_identified/instances))
