#include <h3/h3api.h>
#include <string>
#include <unordered_map>
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
  std::istream& file = std::cin;
  std::string line;
  std::vector<std::string> columns;
  // read the first line and get the columns
  std::getline(file, line);
  // split it by commas and add the columns to the vector
  std::istringstream iss(line);
  std::string token;
  // skip the first column
  std::getline(iss, token, ',');
  // Get the columns
  while (std::getline(iss, token, ',')) {
    columns.push_back(token);
  }
  if (columns.size() > 4) {
    columns.pop_back(); // last columns brake it for some reason
    columns.pop_back();
    columns.pop_back();
    columns.pop_back();
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

  // Iterate over the hexes, find the neighbors and sum the values
  H3Index neighbors[7];
  #pragma omp parallel for private(neighbors)
  for (const auto& hex : hex_ids) {
    gridDisk(hex, 1, neighbors); // assume no error ;)
    // Iterate over the neighbors
    for (auto& neighbor : neighbors) {
      // check if the neighbor is the same as the hex and if it is in the map
      if (neighbor == hex or hexes.find(neighbor) == hexes.end()) {
        continue;
      }
      // Iterate over the columns
      for (auto& column : columns) {
        std::string col_name = column + "_neighbor_sum";
        // only add the neighbor to existing hexes
        #pragma omp atomic
        hexes[hex][col_name] += hexes[neighbor][column];
      }
    }
  }
  std::cout << "hex_id";
  for (auto& column : columns) {
    std::cout << "," << column;
    std::cout << "," << column << "_neighbor_sum";
  }
  std::cout << "\n";
  // Write the data
  for (auto& hex : hexes) {
    std::cout << std::hex << hex.first;
    for (auto& column : columns) {
      std::cout << "," << hex.second[column];
      std::string col_name = column + "_neighbor_sum";
      std::cout << "," << hex.second[col_name];
    }
    std::cout << "\n";
  }
  return 0;
}
