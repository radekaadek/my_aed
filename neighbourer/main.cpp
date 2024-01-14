#include <h3/h3api.h>
#include <string>
#include <unordered_map>
#include <iostream>
#include <vector>
#include <omp.h>

int main() {
  // Read a csv file from stdin with structure:
  // hex_id,bar,school,restaurant,cafe...
  // 8a2a1072b59ffff,238,42389,12,538...
  // 8a2a1072b5bffff,432,0,23,482...
  // add _neighbour_count that sum values of neighbours
  
  std::vector<std::string> headers;
  std::unordered_map<H3Index, std::unordered_map<std::string, float>> hexes;
  std::string line;
  std::getline(std::cin, line);
  // split by comma
  std::string delimiter = ",";
  size_t pos = 0;
  std::string token;
  // skip the hex_id
  token = line.substr(0, line.find(delimiter));
  line.erase(0, line.find(delimiter) + delimiter.length());
  // get the headers
  while ((pos = line.find(delimiter)) != std::string::npos) {
    token = line.substr(0, pos);
    headers.push_back(token);
    line.erase(0, pos + delimiter.length());
  }
  headers.push_back(line);

  // read the data
  while (std::getline(std::cin, line)) {
    // get the hex_id
    token = line.substr(0, line.find(delimiter));
    H3Index hex_id = std::stoull(token, nullptr, 16);
    line.erase(0, line.find(delimiter) + delimiter.length());
    // get the values
    std::unordered_map<std::string, float> values;
    while ((pos = line.find(delimiter)) != std::string::npos) {
      token = line.substr(0, pos);
      values[headers[values.size()]] = std::stof(token);
      line.erase(0, pos + delimiter.length());
    }
    values[headers[values.size()]] = std::stof(line);
    hexes[hex_id] = values;
  }

  // add neighbour sums
  #pragma omp parallel for
  for (size_t i = 0; i < hexes.size(); i++) {
    auto hex = hexes.begin();
    std::advance(hex, i);
    for (const auto& header : headers) {
      H3Index neighbors[7]; // 6 neighbors + self
      gridDisk(hex->first, 1, neighbors);
      float sum = 0;
      #pragma omp parallel for reduction(+:sum)
      for (int j = 0; j < 7; j++) {
        // check if neighbour is in the map
        if (hexes.find(neighbors[j]) != hexes.end() and neighbors[j] != hex->first) {
          sum += hexes[neighbors[j]][header];
        }
      }
      std::string neighbor_name = header + "_neighbour_count";
      hexes[hex->first][neighbor_name] = sum;
    }
  }

  std::cout << "hex_id";
  for (const auto& header : headers) {
    std::cout << "," << header << "," << header << "_neighbour_count";
  }
  std::cout << '\n';
  for (const auto& hex : hexes) {
    std::cout << std::hex << hex.first;
    for (const auto& header : headers) {
      std::cout << "," << hexes[hex.first][header];
      std::cout << "," << hexes[hex.first][header + "_neighbour_count"];
    }
    std::cout << '\n';
  }

  return 0;
}
