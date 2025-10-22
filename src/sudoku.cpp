// The sudoku 9x9 solver (TS9S)
//
//
// This algorithm iterate over all free elements which can be in cells, finding
// place where count of possible digit can be only one and place it. Then made
// it repeatedly.
//
// Artem Ivanov, MIPT, Phystech-School AMCS.
// Oct 2025

#include <chrono>    //working time
#include <fstream>   //csv output
#include <iostream>  //std lib
#include <vector>    //vector lib
#include <stack>     //stack for guesses
#include <limits>    //for numeric_limits

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


  int Count() const { return count_; }

  // set this cell to exactly one number (used for a guess)
  void SetSingle(int num) {
    for (int i = 0; i < cSheetSize; ++i) {
      IsPosible_[i] = false;
    }
    IsPosible_[num - 1] = true;
    count_ = 1;
  }

  // get list of possible numbers (non-owning small vector)
  std::vector<int> PossibleNumbers() const {
    std::vector<int> res;
    for (int i = 0; i < cSheetSize; ++i) {
      if (IsPosible_[i]) res.push_back(i + 1);
    }
    return res;
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



  // detect impossible cell (no possibilities and not origin)
  bool HasContradiction(const std::vector<std::vector<int>>& field) const {
    for (int i = 0; i < cSheetSize; ++i) {
      for (int j = 0; j < cSheetSize; ++j) {
        if (not draw_field_[i][j].IsOrigin() && draw_field_[i][j].Count() <= 0) {
          return true;
        }
        // also check that existing origins do not violate basic rules:
        if (field[i][j] != 0) {
          int val = field[i][j];
          // check row
          for (int k = 0; k < cSheetSize; ++k) {
            if (k != j && field[i][k] == val) return true;
          }
          // check column
          for (int k = 0; k < cSheetSize; ++k) {
            if (k != i && field[k][j] == val) return true;
          }
          // check block
          for (int k = i / 3 * 3; k < i / 3 * 3 + 3; ++k) {
            for (int l = j / 3 * 3; l < j / 3 * 3 + 3; ++l) {
              if ((k != i || l != j) && field[k][l] == val) return true;
            }
          }
        }
      }
    }
    return false;
  }

  // get count of possibilities for a cell
  int GetCount(int i, int j) const { return draw_field_[i][j].Count(); }

  // get possible numbers list for given cell
  std::vector<int> GetPossibleNumbers(int i, int j) const {
    return draw_field_[i][j].PossibleNumbers();
  }

  // check if a specific number is possible in cell
  bool IsPossible(int i, int j, int num) const { return draw_field_[i][j].IsPos(num); }

  // apply assigning a number to cell both in draw_field and field (for guesses)
  void ApplyAssignment(std::vector<std::vector<int>>& field, int i, int j, int num) {
    // set field
    field[i][j] = num;
    // make cell origin in draw_field and set only this possibility
    draw_field_[i][j].SetSingle(num);
    draw_field_[i][j].MakeOrigin();
    --count_free_cells_;
  }

  
};

void Printing(std::vector<std::vector<int>>& field,
              std::vector<std::vector<bool>>& is_input, bool to_console = true,
              bool to_csv = true,
              bool highlight = true);  // function to get output

void Input(std::vector<std::vector<int>>& field,
           std::vector<std::vector<bool>>& is_input,
           DrawField& draw_field, char* in[]);  // function which get input

// Snapshot structure for backtracking (stores entire state)
struct Snapshot {
  std::vector<std::vector<int>> field;
  std::vector<std::vector<bool>> is_input;
  DrawField draw_field;
  int guess_i;
  int guess_j;
  std::vector<int> candidates;
  int next_candidate_index;
};

int main(int argc, char* argv[]) {
  std::vector<std::vector<int>> field = std::vector<std::vector<int>>(
      cSheetSize, std::vector<int>(cSheetSize, 0));  // main field
  std::vector<std::vector<bool>> is_input = std::vector<std::vector<bool>>(
      cSheetSize,
      std::vector<bool>(cSheetSize, false));  // field which store start field

  DrawField draw_field;  // draw field

  Input(field, is_input, draw_field, argv);

  std::cout << "processing...\n";

  auto start = std::chrono::high_resolution_clock::now();  // start timepoint

  // stack of snapshots for DFS/backtracking of guesses
  std::stack<Snapshot> st;

  bool solved = false;
  bool failed = false;

  while (true) {
    // 1) apply deterministic filling until no single-candidate cells remain
    bool progress = true;
    while (progress) {
      progress = draw_field.Filling(field);
      // after each filling step check for contradiction
      if (draw_field.HasContradiction(field)) {
        break;
      }
    }

    if (draw_field.HasContradiction(field)) {
      // contradiction -> need to backtrack
      if (st.empty()) {
        failed = true;
        break;
      } else {
        // pop snapshots until we find one with remaining candidates
        bool restored = false;
        while (!st.empty()) {
          Snapshot snap = st.top();
          st.pop();
          if (snap.next_candidate_index + 1 < static_cast<int>(snap.candidates.size())) {
            // try next candidate for this snapshot
            int next_idx = snap.next_candidate_index + 1;
            int ni = snap.guess_i;
            int nj = snap.guess_j;
            int candidate = snap.candidates[next_idx];

            // restore state
            field = snap.field;
            is_input = snap.is_input;
            draw_field = snap.draw_field;

            // push updated snapshot with incremented index back (so we can try further later)
            snap.next_candidate_index = next_idx;
            st.push(snap);

            // apply next candidate and continue solving
            draw_field.ApplyAssignment(field, ni, nj, candidate);
            restored = true;
            break;
          } else {
            // no more candidates in this snapshot -> continue popping
            continue;
          }
        }
        if (!restored) {
          // no snapshot left to try
          failed = true;
          break;
        } else {
          // continue main loop after applying candidate
          continue;
        }
      }
    }

    // if no contradiction and no free cells -> solved
    if (draw_field.CountFreeCells() == 0) {
      solved = true;
      break;
    }

    // if no progress but still free cells -> make a guess
    // find a cell with minimal >1 candidates
    int best_i = -1, best_j = -1;
    int best_count = std::numeric_limits<int>::max();
    for (int i = 0; i < cSheetSize; ++i) {
      for (int j = 0; j < cSheetSize; ++j) {
        if (!draw_field.IsPossible(i, j, 0 + 1) && !draw_field.IsPossible(i, j, 9 + 1)) {
          //
        }
        // we need cells which are not origin
        // GetCount returns count of possibilities
        int cnt = draw_field.GetCount(i, j);
        if (not draw_field.GetPossibleNumbers(i, j).empty() && !draw_field.GetPossibleNumbers(i, j).empty()) {
          //
        }
        if (cnt > 1 && cnt < best_count) {
          best_count = cnt;
          best_i = i;
          best_j = j;
        }
      }
    }

    // If we failed to find a suitable cell (shouldn't happen) -> fail
    if (best_i == -1) {
      failed = true;
      break;
    }

    // prepare candidates
    std::vector<int> candidates = draw_field.GetPossibleNumbers(best_i, best_j);
    if (candidates.empty()) {
      // no possible candidates -> contradiction
      if (st.empty()) {
        failed = true;
        break;
      } else {
        // will be handled on next loop iteration by HasContradiction check
        continue;
      }
    }

    // save snapshot BEFORE trying first candidate
    Snapshot snap;
    snap.field = field;
    snap.is_input = is_input;
    snap.draw_field = draw_field;
    snap.guess_i = best_i;
    snap.guess_j = best_j;
    snap.candidates = candidates;
    snap.next_candidate_index = 0;
    st.push(snap);

    // apply first candidate
    int first_candidate = candidates[0];
    draw_field.ApplyAssignment(field, best_i, best_j, first_candidate);

    // loop continues
  }

  auto end = std::chrono::high_resolution_clock::now();  // end timepoint

  double mseconds =
      std::chrono::duration_cast<std::chrono::milliseconds>(end - start)
          .count();  // calculate time of proccessing

  if (solved) {
    std::cout << "done!\n"
              << "process done in " << mseconds << "ms\n";
    Printing(field, is_input, true, true, true);  // printing
  } else {
    std::cout << "failed to find a solution (contradiction or no candidates)\n"
              << "elapsed " << mseconds << "ms\n";
    Printing(field, is_input, true, true, true);  // partial/last state printing
  }

  return 0;
}

void Printing(std::vector<std::vector<int>>& field,
              std::vector<std::vector<bool>>& is_input, bool to_console,
              bool to_csv, bool highlight) {
  std::ofstream out_csv;
  if (to_csv) {
    out_csv.open("./out.csv");
    out_csv << ",,,,,,,,\n";
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
           std::vector<std::vector<bool>>& is_input, DrawField& draw_field, char* in[]) {
  for (int i = 0; i < cSheetSize; ++i) {
    for (int j = 0; j < cSheetSize; ++j) {
      int cur_num = in[i*9+j+1][0] - '0';
      if(in[i*9+j+1][0] == '#'){
        cur_num = 0;
      }
      field[i][j] = cur_num;
      if (cur_num != 0) {
        is_input[i][j] = true;
        draw_field.DecreaseCountFree();
        draw_field.MakeOrigin(i, j);
      }
    }
  }
};
