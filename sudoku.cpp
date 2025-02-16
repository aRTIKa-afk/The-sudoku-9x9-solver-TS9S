// The sudoku 9x9 solver (TS9S)
//
//
// This algorithm iterate over all free elements which can be in cells, finding
// place where count of possible digit can be only one and place it. Then made
// it repeatedly.
//
// Artem Ivanov, MIPT, Phystech-School AMCS.
// Feb 2025

#include <chrono>    //working time
#include <fstream>   //csv output
#include <iostream>  //std lib
#include <vector>    //vector lib

const int cSheetSize = 9;  // size of sheet

class Cells {  // class for draw cell
 private:
  std::vector<bool> IsPosible_ = std::vector<bool>(cSheetSize, true);
  int count_ = cSheetSize;
  bool origin_ = false;

 public:
  bool IsLast() const { return count_ == 1; }
  bool IsOrigin() const { return origin_; }
  bool IsPos(int num) const { return IsPosible_[num - 1]; }
  void MakeOrigin() { origin_ = true; }
  void DecreaseCount() { --count_; }
  void ChangePosibility(int num) { IsPosible_[num - 1] = false; }
  int LastNumber() {
    for (int i = 0; i < cSheetSize; ++i) {
      if (IsPosible_[i]) {
        return i + 1;
      }
    }
    return 0;
  }
};

class DrawField {  // class for draw field
 private:
  int count_free_cells_ = cSheetSize * cSheetSize;
  std::vector<std::vector<Cells>> draw_field_ = std::vector<std::vector<Cells>>(
      cSheetSize, std::vector<Cells>(cSheetSize));

 public:
  void MakeOrigin(int i, int j) { draw_field_[i][j].MakeOrigin(); }
  void DecreaseCountFree() { --count_free_cells_; }
  void IncreaseCountFree() { ++count_free_cells_; }
  int CountFreeCells() const { return count_free_cells_; }

  bool Filling(std::vector<std::vector<int>>& field) {
    bool updated = false;
    for (int i = 0; i < cSheetSize; ++i) {
      for (int j = 0; j < cSheetSize; ++j) {
        if (not draw_field_[i][j].IsOrigin()) {
          for (int k = 0; k < cSheetSize; ++k) {
            if (field[i][k] != 0 && draw_field_[i][j].IsPos(field[i][k])) {
              draw_field_[i][j].DecreaseCount();
              draw_field_[i][j].ChangePosibility(field[i][k]);
            }
          }
          for (int k = 0; k < cSheetSize; ++k) {
            if (field[k][j] != 0 && draw_field_[i][j].IsPos(field[k][j])) {
              draw_field_[i][j].DecreaseCount();
              draw_field_[i][j].ChangePosibility(field[k][j]);
            }
          }
          for (int k = i / 3 * 3; k < i / 3 * 3 + 3; ++k) {
            for (int l = j / 3 * 3; l < j / 3 * 3 + 3; ++l) {
              if (field[k][l] != 0 && draw_field_[i][j].IsPos(field[k][l])) {
                draw_field_[i][j].DecreaseCount();
                draw_field_[i][j].ChangePosibility(field[k][l]);
              }
            }
          }
        }
      }
    }

    for (int i = 0; i < cSheetSize; ++i) {
      for (int j = 0; j < cSheetSize; ++j) {
        if (not draw_field_[i][j].IsOrigin() && draw_field_[i][j].IsLast()) {
          draw_field_[i][j].MakeOrigin();
          field[i][j] = draw_field_[i][j].LastNumber();
          --count_free_cells_;
          updated = true;
        }
      }
    }
    return updated;
  }
};

void Printing(std::vector<std::vector<int>>& field,
              std::vector<std::vector<bool>>& is_input, bool to_console = true,
              bool to_csv = true,
              bool highlight = true);  // function to get output

void Input(std::vector<std::vector<int>>& field,
           std::vector<std::vector<bool>>& is_input,
           DrawField& draw_field);  // function which get input

int main() {
  std::vector<std::vector<int>> field = std::vector<std::vector<int>>(
      cSheetSize, std::vector<int>(cSheetSize, 0));  // main field
  std::vector<std::vector<bool>> is_input = std::vector<std::vector<bool>>(
      cSheetSize,
      std::vector<bool>(cSheetSize, false));  // field which store start field

  DrawField draw_field;  // draw field

  Input(field, is_input, draw_field);

  std::cout << "processing...\n";

  auto start = std::chrono::high_resolution_clock::now();  // start timepoint

  while (draw_field.CountFreeCells() != 0) {
    if (draw_field.Filling(field)) {
      continue;  // recursively place one-possible digit
    }
    // Will be soon
  }

  auto end = std::chrono::high_resolution_clock::now();  // end timepoint

  double mseconds =
      std::chrono::duration_cast<std::chrono::milliseconds>(end - start)
          .count();  // calculate time of proccessing

  std::cout << "done!\n"
            << "process done in " << mseconds << "ms\n";

  Printing(field, is_input, true, false, true);  // printing
}

void Printing(std::vector<std::vector<int>>& field,
              std::vector<std::vector<bool>>& is_input, bool to_console,
              bool to_csv, bool highlight) {
  std::ofstream out_csv;
  if (to_csv) {
    out_csv.open("./out.csv");
  }
  std::string highlight_green = "\x1b[32m\x1b[1m\x1b[4m";
  std::string highlight_yellow = "\x1b[33m\x1b[2m";
  std::string highlight_zero = "\x1b[0m";
  if (not highlight) {
    highlight_green = "";
    highlight_yellow = "";
    highlight_zero = "";
  }
  for (int i = 0; i < cSheetSize; ++i) {
    for (int j = 0; j < cSheetSize; ++j) {
      if (to_console) {
        if (not is_input[i][j]) {
          std::cout << highlight_green << static_cast<char>(field[i][j] + '0')
                    << highlight_zero << ' ';
        } else {
          std::cout << highlight_yellow << static_cast<char>(field[i][j] + '0')
                    << highlight_zero << ' ';
        }
      }
      if (out_csv.is_open()) {
        out_csv << field[i][j];
      }
      if (out_csv.is_open() && j < cSheetSize - 1) {
        out_csv << ',';
      }
    }
    if (to_console) {
      std::cout << '\n';
    }
    if (out_csv.is_open()) {
      out_csv << '\n';
    }
  }
  if (to_console) {
    std::cout << "\n\n\n";
  }
  if (to_csv) {
    out_csv.close();
  }
}

void Input(std::vector<std::vector<int>>& field,
           std::vector<std::vector<bool>>& is_input, DrawField& draw_field) {
  for (int i = 0; i < cSheetSize; ++i) {
    for (int j = 0; j < cSheetSize; ++j) {
      int cur_num = 0;
      std::cin >> cur_num;
      field[i][j] = cur_num;
      if (cur_num != 0) {
        is_input[i][j] = true;
        draw_field.DecreaseCountFree();
        draw_field.MakeOrigin(i, j);
      }
    }
  }
};