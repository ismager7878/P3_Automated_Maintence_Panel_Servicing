#include "fstream"
#include "iostream"
#include "csvManager.hpp"

#include <filesystem>

using namespace std;

namespace CsvManager{

    // Constructor implementation
    CsvFile::CsvFile(string filePath, vector<string> headers) : filePath(filePath), headers(headers) {
        if(!this->isCsvFile(filePath)){
            throw invalid_argument("File path must end with .csv");
        }

        this->filePath = "tests/" + filePath;

        // Create directory if it doesn't exist
        filesystem::path path(this->filePath);
        filesystem::path dir = path.parent_path();
        if (!dir.empty() && !filesystem::exists(dir)) {
            filesystem::create_directories(dir);
            cout << "Created directory: " << dir << endl;
        }

        if(filesystem::exists(this->filePath)){
            int fileIndex = 1;
            string baseFilePath = this->filePath;
            while(filesystem::exists(this->filePath)){
                this->filePath = baseFilePath.substr(0, baseFilePath.find_last_of('.')) + "_" + to_string(fileIndex) + ".csv";
                fileIndex++;
            }
            cout << "File exists, using: " << this->filePath << endl;
        }

        fstream fout;
        try {
            fout.open(this->filePath, ios::out | ios::app);
            if (!fout.is_open()) {
                throw runtime_error("Failed to open file for writing");
            }
            cout << "Creating file at: " << this->filePath << endl;
        } catch (const std::exception& e) {
            cerr << "Error creating file: " << e.what() << endl;
            throw;
        }

        for(size_t i = 0; i < headers.size(); i++){
            fout << headers[i];
            if(i != headers.size() -1){
                fout << ",";
            }
        }
        fout << "\n";
        fout.close();
    }

    vector<string> CsvFile::getHeaders(){
        return this->headers;
    }

    int CsvFile::addRows(vector<vector<string>> newRows){
        fstream fout;
        
        fout.open(this->filePath, ios::out | ios::app);
        
        if (!fout.is_open()) {
            cerr << "Error: Could not open file for writing: " << this->filePath << endl;
            return -1;
        }

        for(size_t i = 0; i < newRows.size(); i++){
            for(size_t j = 0; j < newRows[i].size(); j++){
                fout << newRows[i][j];
                if(j != newRows[i].size() -1){
                    fout << ",";
                }
            }
            fout << "\n";
            this->rows.push_back(newRows[i]);
        }

        cout << "Added " << newRows.size() << " rows to " << this->filePath << endl;

        fout.close();
        return 0;
    }

    int CsvFile::addRow(vector<string> newRow){
        return this->addRows({newRow});
    }

    bool CsvFile::isCsvFile(string path){
        return path.substr(path.find_last_of('.') + 1) == "csv";
    }

} // namespace CsvManager
