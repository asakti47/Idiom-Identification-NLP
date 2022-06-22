from re import I
from xml.etree.ElementInclude import include
import jsonlines
import string
import ahocorasick as ac


from dis import dis
import gensim.downloader
from gensim.models import KeyedVectors
import scipy

#glove_vectors = gensim.downloader.load('glove-wiki-gigaword-300')
#glove_vectors.save('glove-wiki-300.model')
glove_vectors = KeyedVectors.load('glove-wiki-300.model')

dictionary_path = "idioms_extended_augmented.txt"
corupus_path = "magpie_unfiltered.jsonl"
#corupus_path = "magpie_test_data.jsonl"

A = ac.Automaton()

ignorable_words_path = "ignorable_words.txt"
wordvec_ignore_words = set()
with open(ignorable_words_path, "r") as f:
    for line in f:
        wordvec_ignore_words.add(line.strip())

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

NEIGHBOR_STRING_COUNT = 10
def neighbor_strings(original, idx, direction):
    curr = ""
    results = []
    while idx >= 0 and idx < len(original):
        if original[idx] in string.whitespace:
            if len(curr) > 0:
                if direction == -1:
                    curr = curr[::-1]
                results.append(curr)
                curr = ""
                if len(results) >= NEIGHBOR_STRING_COUNT:
                    break
        elif original[idx] in string.ascii_letters or original[idx] in string.digits:
            curr += original[idx]

        idx += direction
    
    if len(curr) > 0 and len(results) < NEIGHBOR_STRING_COUNT:
        if direction == -1:
            curr = curr[::-1]
        results.append(curr)
    
    return results
    
CLOSEST_NEIGHBOR_COUNT = 2
def average_distance(target, neighbors):
    if target not in glove_vectors:
        return 1
    target_vector = glove_vectors[target]
    results = []
    for neighbor in neighbors:
        if neighbor not in glove_vectors or neighbor in wordvec_ignore_words:
            continue
        neighbor_vector = glove_vectors[neighbor]
        results.append(scipy.spatial.distance.cosine(target_vector, neighbor_vector))
    
    results.sort()
    count = 0
    sum = 0
    for i in range(min(len(results), CLOSEST_NEIGHBOR_COUNT)):
        sum += results[i]
        count += 1

    if count == 0:
        return 1
    return sum / count

    

# Load corpus
instances = 0
total_identified = 0
accurately_identified = 0
curr = 0
print("Running tests\n")
identification_scores = []
with jsonlines.open(corupus_path) as reader:
    for instance in reader:
        curr += 1
        print("\r{}".format(curr), end="")
        if instance["confidence"] == 1.0:
            instances += 1
            idiom_begin = instance["offsets"][0][0]
            idiom_end = instance["offsets"][-1][1] - 1
            context_list = instance["context"]


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
                    if start_index != 0 and context[start_index - 1] in string.ascii_letters:
                        continue
                    
                    if end_index != len(context) - 1 and context[end_index + 1] in string.ascii_letters:
                        continue
                    
                    accurate = idiom_begin == indices[start_index] and curr_idiom_end == indices[end_index]
                    
                    neighbors = neighbor_strings(context, start_index - 1, -1)
                    neighbors.extend(neighbor_strings(context, end_index + 1, 1)) # check edge here
                    
                    distances = []
                    original_words = original_value.split(" ")
                    for original_word in original_words:
                        if original_word in wordvec_ignore_words:
                            continue
                        distances.append(average_distance(original_word, neighbors))
                    
                    distance = 0
                    distances.sort()
                    FALLOFF_FACTOR = .9
                    curr_factor = 1
                    max_distance = 0
                    for d in distances:
                        distance += d * curr_factor
                        max_distance += curr_factor
                        curr_factor *= FALLOFF_FACTOR
                    if max_distance == 0:
                        max_distance = 1
                        
                    distance /= max_distance

                    identification_scores.append((distance, accurate))

        
      
identification_scores.sort()
identification_scores.reverse()

def f_score(precision, recall):
    if precision == 0 or recall == 0:
        return 0
    return 2 / (1 / precision + 1 / recall)

best_alpha = 0
best_f_score = 0
best_precision = 0
best_recall = 0 
index = 0

for identified in identification_scores:
    if identified[1]:
        accurately_identified += 1
    total_identified += 1
    recall = accurately_identified / instances
    precision = accurately_identified / total_identified
    f = f_score(precision, recall)
    if f > best_f_score:
        best_alpha = identified[0]
        best_f_score = f
    index += 1
    if index % 500 == 0:
        print("\nPrecision: {}\n Recall: {}\n Alpha: {}\n F-score: {}\n".format(precision, recall, identified[0], f))
    
    

print("\n\nBest alpha: {}\nBest F-score: {}".format(best_alpha, best_f_score))

print("")
print("Precision: " + str(accurately_identified/total_identified))
print("Recall: " + str(accurately_identified/instances))
print("F-score: " + str(f_score(accurately_identified/total_identified, accurately_identified/instances)))
