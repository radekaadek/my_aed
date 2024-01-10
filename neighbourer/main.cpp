#include <cstdio>
#include <h3/h3api.h>
#include <string>
#include <unordered_map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>

int main() {
  // Read a csv file with the structure:
  // hex_id,bar,school,restaurant,cafe...
  // 8a2a1072b59ffff,238,42389,12,538...
  // 8a2a1072b5bffff,432,0,23,482...
  // add _neighbor_count that sum values of neighbors
  
  std::unordered_map<H3Index, std::unordered_map<std::string, float>> hexes;
  std::ifstream file("osm_data.csv");
  // Check if the file was opened
  if (!file.is_open()) {
    std::cout << "Error opening file" << '\n';
    return 1;
  }
  std::string line;
  std::vector<std::string> columns;
  // Read the header
  std::getline(file, line);
  // split it by commas
  std::istringstream iss(line);
  // read the first token which is the hex_id
  std::getline(iss, line, ',');
  for (std::string token; std::getline(iss, token, ',');) {
    // Add the header to the hexes
    hexes[H3Index()].emplace(token, 0);
    columns.push_back(token);
  }

  // Read the rest of the file setting the values to the hexes
  while (std::getline(file, line)) {
    // split it by commas
    std::istringstream iss(line);
    std::string token;
    // Get the hex id
    std::getline(iss, token, ',');
    H3Index hex_id = H3Index(std::stoull(token, nullptr, 16));
    // Iterate over the columns
    for (auto& column : columns) {
      // Get the value
      std::getline(iss, token, ',');
      // Add the value to the hex
      hexes[hex_id][column] = std::stof(token);
    }
  }
  std::vector<H3Index> hex_ids;
  for (auto& hex : hexes) {
    hex_ids.push_back(hex.first);
  }
  size_t saved_hexes = hex_ids.size();

  // Iterate over the hexes, find the neighbors and sum the values
  H3Index neighbors[7];
  for (const auto& hex : hex_ids) {
    // H3Error error = gridDisk(H3Index origin, int k, H3Index *out)
    H3Error error = gridDisk(hex, 1, neighbors); // assume no error ;)
    // Iterate over the neighbors
    for (auto& neighbor : neighbors) {
      // check if the neighbor is the same as the hex and if it is in the map
      if (neighbor == hex or hexes.find(neighbor) == hexes.end()) {
        continue;
      }
      // Iterate over the columns
      for (auto& column : columns) {
        std::string col_name = column + "_neighbor_count";
        // only add the neighbor to existing hexes
        hexes[hex][col_name] += hexes[neighbor][column];
      }
    }
  }
  // create the output file
  FILE* output_file = fopen("osm_with_neighbours.csv", "w");
  // Write the header
  fprintf(output_file, "hex_id");
  for (auto& column : columns) {
    fprintf(output_file, ",%s", column.c_str());
    fprintf(output_file, ",%s", (column + "_neighbor_count").c_str());
  }
  fprintf(output_file, "\n");
  // Write the data
  for (auto& hex : hexes) {
    fprintf(output_file, "%lx", hex.first);
    for (auto& column : columns) {
      fprintf(output_file, ",%f", hex.second[column]);
      std::string col_name = column + "_neighbor_count";
      fprintf(output_file, ",%f", hex.second[col_name]);
    }
    fprintf(output_file, "\n");
  }
  fclose(output_file);
  return 0;
}
