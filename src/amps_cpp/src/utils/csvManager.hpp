#ifndef CSV_MANAGER_HPP
#define CSV_MANAGER_HPP

#include <string>
#include <vector>

using namespace std;

namespace CsvManager{

    class CsvFile {
    public:
        CsvFile(string filePath, vector<string> headers);

        vector<string> getHeaders();

        int addRows(vector<vector<string>> newRows);

        int addRow(vector<string> newRow);
    private:
        string filePath;
        vector<string> headers;
        vector<vector<string>> rows;

        bool isCsvFile(string path);
    
    };

}



#endif // CSV_MANAGER_HPP