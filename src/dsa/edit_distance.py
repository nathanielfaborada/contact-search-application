"""
Edit Distance (Levenshtein Distance) Algorithm & Universal Search Engine
Time Complexity: O(m * n)
Space Complexity: O(m * n)
where m = length of query, n = length of target string
"""


def edit_distance(first_string, second_string):
    """Computes the minimum single-character edits (insertions, deletions, substitutions)

    required to convert first_string into second_string.
    """
    first_string_length = len(first_string)
    second_string_length = len(second_string)
    distance_table = [
        [0] * (second_string_length + 1)
        for _ in range(first_string_length + 1)
    ]

    for row_index in range(first_string_length + 1):
        distance_table[row_index][0] = row_index
    for col_index in range(second_string_length + 1):
        distance_table[0][col_index] = col_index

    for row_index in range(1, first_string_length + 1):
        for col_index in range(1, second_string_length + 1):
            substitution_cost = (
                0 if first_string[row_index - 1] == second_string[col_index - 1] else 1
            )
            distance_table[row_index][col_index] = min(
                distance_table[row_index - 1][col_index] + 1,       # Deletion
                distance_table[row_index][col_index - 1] + 1,       # Insertion
                distance_table[row_index - 1][col_index - 1] + substitution_cost  # Substitution
            )

    return distance_table[first_string_length][second_string_length]


def find_closest_contacts(search_query_number, contacts_directory):
    """Finds all contacts whose phone number has the minimum edit distance to the search query."""
    if not contacts_directory or not search_query_number:
        return {}

    scored_contacts = sorted(
        contacts_directory.items(),
        key=lambda contact_entry: edit_distance(search_query_number, contact_entry[1])
    )

    minimum_distance = edit_distance(search_query_number, scored_contacts[0][1])
    return {
        contact_name: contact_phone
        for contact_name, contact_phone in scored_contacts
        if edit_distance(search_query_number, contact_phone) == minimum_distance
    }


def search_and_rank_records(
    records_list,
    query_string="",
    active_department="All",
    only_favorites=False
):
    """Filters and ranks ContactRecord objects based on query, department tag, and favorite filter.

    Returns a tuple of (filtered_records_list, distance_scores_dict).
    """
    filtered_list = []
    distance_scores = {}

    query_clean = query_string.strip()
    is_numeric_query = query_clean.isdigit() if query_clean else False
    query_lower = query_clean.lower()

    # Step 1: Base filtering (Department tag and Favorites)
    candidates = []
    for record in records_list:
        if only_favorites and not record.is_favorite:
            continue
        if active_department != "All" and record.department != active_department:
            continue
        candidates.append(record)

    if not query_clean:
        return candidates, {}

    # Step 2: Query matching
    if is_numeric_query:
        # Numeric query: Levenshtein distance on phone numbers
        scored = []
        for record in candidates:
            dist = edit_distance(query_clean, record.phone_number)
            scored.append((record, dist))

        if scored:
            scored.sort(key=lambda item: item[1])
            min_dist = scored[0][1]
            # Take closest matches (within min_dist + 1 for flexible fuzzy tolerance)
            for record, dist in scored:
                if dist <= min_dist + 1:
                    filtered_list.append(record)
                    distance_scores[record.full_name] = dist
    else:
        # Text query: Multi-field keyword matching (Name, Department, Email, Notes, Office)
        for record in candidates:
            match_found = False
            if query_lower in record.full_name.lower():
                match_found = True
            elif query_lower in record.department.lower():
                match_found = True
            elif query_lower in record.email.lower():
                match_found = True
            elif query_lower in record.office.lower():
                match_found = True
            elif query_lower in record.notes.lower():
                match_found = True

            if match_found:
                filtered_list.append(record)

    return filtered_list, distance_scores
