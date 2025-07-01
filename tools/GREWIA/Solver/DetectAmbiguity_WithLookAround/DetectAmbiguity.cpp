#include <cmath>
#include <map>
#include <list>
#include <bitset>
#include <queue>
#include <iostream>
#include <fstream>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <random>
#include <openssl/evp.h>
#include <queue>
#include <chrono>

#include "DetectAmbiguity.h"


namespace solverbin{

  std::string base64_encode(const std::string &input) {
      // 计算编码后的大小
      int len = 4 * ((input.length() + 2) / 3);
      char *encoded = new char[len + 1];

      // 编码
      EVP_EncodeBlock((unsigned char*)encoded, (const unsigned char*)input.c_str(), input.length());

      std::string result(encoded);
      delete[] encoded;
      return result;
  }

  bool RunningCmd(std::string cmd){
    auto start = std::chrono::high_resolution_clock::now();
    system(cmd.c_str());
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    if (duration.count() >= 1000){
      std::cout << "Execution time: " << duration.count() << " ms" << std::endl;
      return true;
    }
    else{
      return false;
    }
  }

  void DetectABTNFA_Lookaround::ComputeAlphabet_Colormap(uint8_t* ByteMap, std::set<uint8_t> &Alphabetp){
		std::set<uint8_t> color_set;
		color_set.insert(ByteMap[0]);
    std::vector<uint8_t> RuneRange;
    ColorMap.insert(std::make_pair(ByteMap[0], RuneRange));
		if (ByteMap[0] != 0){
      Alphabet.insert(0);
      RuneRange.emplace_back(0);
    }
		for (int i = 0; i < 256; i++){
      auto Color2Range = ColorMap.find(ByteMap[i]);
			if (color_set.find(ByteMap[i]) != color_set.end()){
        Color2Range->second.emplace_back(i);
      }
			else{
        std::vector<uint8_t> Range;
				color_set.insert(ByteMap[i]);
        Range.emplace_back(i);
        ColorMap.insert(std::make_pair(ByteMap[i], Range));
				if (ByteMap[i] != 0)
					Alphabet.insert(i);
			}
		}
	}

  bool DetectABTNFA_Lookaround::Verify(std::string& attack_string_file){
    int time = length / 100000;
    std::string time_str = std::to_string(time);
    std::string matching_function;
    if (MatchingFunction == "0"){
      matching_function = "1";
    }
    else{
      matching_function = "0";
    }    
    
    if (RegexEngine == "Java"){
      std::string cmd = "timeout " +  time_str + "s /app/engines/java8/bin/benchmark " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "JavaScript"){
      std::string cmd = "timeout " +  time_str + "s /app/engines/nodejs21/bin/benchmark " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "Perl"){
      std::string cmd = "timeout " +  time_str + "s perl /app/engines/perl/benchmark.pl " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "PHP"){
      std::string cmd = "timeout " +  time_str + "s php /app/engines/php/benchmark.php " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "Python"){  
      std::string cmd = "timeout " +  time_str + "s python3 /app/engines/python/benchmark.py " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "Boost"){
      std::string cmd = "timeout " +  time_str + "s /app/engines/cpp/bin/benchmark " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "C#"){    
      std::string cmd = "timeout " +  time_str + "s /app/engines/csharp/bin/benchmark " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "Go"){
      std::string cmd = "timeout " +  time_str + "s /app/engines/go/bin/benchmark " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "Rust"){
      std::string cmd = "timeout " +  time_str + "s /app/engines/rust/bin/benchmark " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "Ruby"){
      std::string cmd = "timeout " +  time_str + "s ruby /app/engines/ruby/benchmark.rb " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else if (RegexEngine == "RE2"){
      std::string cmd = "timeout " +  time_str + "s /app/engines/re2/bin/benchmark " + base64_encode(Regex) + " " + attack_string_file + " " + matching_function;
      return RunningCmd(cmd);
    }
    else{
      std::cout << "Regex engine not supported" << std::endl;
      return false;
    }
  }

  void DetectABTNFA_Lookaround::DumpAlphabet(std::set<uint8_t>& A){
    std::cout << "The alphabet: ";
    for (auto it : A){
      std::cout << int(it) << " ";
    }
    std::cout << "" << std::endl;
  }


  std::string DetectABTNFA_Lookaround::GenerateRandomWitness(std::string& WitnessStr){
    std::string WritenStr;
    for (uint8_t color : WitnessStr){
      std::random_device rd;                                // 随机设备
      std::mt19937 gen(rd());                               // 随机数生成器
      auto Range = ColorMap.find(e1.ByteMap[color])->second;
      std::uniform_int_distribution<> dis(0, Range.size() - 1); // 均匀分布
      int randomIndex = dis(gen);
      WritenStr.push_back(Range[randomIndex]);
    }
    return WritenStr;
  }

  bool DetectABTNFA_Lookaround::Writefile(){
    attack_string = InterStr + WitnessStr;
    auto initState = solverbin::FollowAtomata(this->e1);
    auto dfa = solverbin::DFA(&initState);
    if (!dfa.Complement(dfa.DState, attack_string, Suffix)) 
      std::cout <<  "no match" << std::endl;
    std::ofstream Outfile;
    NumberOfCandidates++;
    if (mkdir(Output.c_str(), 0777) == 0) {
      std::cout << "Directory created successfully: " << Output << std::endl;
    } 
    // else {
    //   std::cerr << "Error: Unable to create directory " << Output << std::endl;
    // }
    std::string attack_string_file = Output + "/" + std::to_string(NumberOfCandidates) + ".txt";
    Outfile.open(attack_string_file);
    if (!Outfile.is_open()) {
      std::cerr << "Failed to open the file." << std::endl;
      return 0;
    }
    if (IsRandom){
      while (attack_string.size() <= length)
        attack_string.append(GenerateRandomWitness(WitnessStr));
    }
    else
      while (attack_string.size() <= length)
        attack_string.append(WitnessStr);
    attack_string.append(Suffix); 
    attack_string.append("\n");
    if (ConsiderReverse == 1)
      attack_string.append(LastWord); 
    Outfile << attack_string;
    std::cout << "file is closed" << std::endl;
    if (Verify(attack_string_file)){
      Suffix.append("\n");
      Outfile.close();
      return true;
    }else{
      std::string cmd = "rm -rf " + attack_string_file;
      system(cmd.c_str());
      Suffix.clear();
      Outfile.close();
      NumberOfCandidates--;
      return false;
    }
  }

  bool DetectABTNFA_Lookaround::WriteInBase64() {
    attack_string = InterStr + WitnessStr;
    auto initState = solverbin::FollowAtomata(this->e1);
    auto dfa = solverbin::DFA(&initState);
    if (!dfa.Complement(dfa.DState, attack_string, Suffix))
      std::cout <<  "no match" << std::endl;
    std::ofstream Outfile;
    NumberOfCandidates++;
    if (mkdir(Output.c_str(), 0777) == 0) {
      std::cout << "Directory created successfully: " << Output << std::endl;
    } else {
      std::cerr << "Error: Unable to create directory " << Output << std::endl;
    }
    Outfile.open(Output + "/" + std::to_string(NumberOfCandidates) + ".txt");
    if (!Outfile.is_open()) {
      std::cerr << "Failed to open the file." << std::endl;
      return 0;
    }
    Outfile << base64_encode(InterStr) << '\n';
    Outfile << base64_encode(WitnessStr) << '\n';
    Outfile << base64_encode(Suffix);
    std::cout << "file is closed" << std::endl;
    Suffix.clear();
    Outfile.close();
    return true;
  }

  DetectABTNFA_Lookaround::DetectABTNFA_Lookaround(REnodeClass r, int l, std::string Path, int Is_Lazy, int Is_Random, int Is_FullMatch, int Consider_Reverse ){
    isLazy = Is_Lazy;
    length = l;
    Output = Path;
    IsRandom = Is_Random;
    ConsiderReverse = Consider_Reverse;
    e1 = r;
    if (ConsiderReverse == 1) {
      LastWord = e1.ReturnLastWord(e1.Renode);
      // std::cout << "reverse: " << e1.REnodeToString(e1.Renode) << std::endl;
    }
    // if (Is_FullMatch == 1)
    e1.matchFlag = REnodeClass::MatchFlag::dollarEnd;
    F1 = FollowAtomata(e1);
    SSBegin = {F1.NState, F1.NState, F1.NState};
    ComputeAlphabet_Colormap(e1.ByteMap, Alphabet);
    if (debug.PrintBytemap) e1.BuildBytemapToString(e1.ByteMap);
    if (debug.PrintAlphabet) DumpAlphabet(Alphabet);
  }

  void DetectABTNFA_Lookaround::DumpTernarySimulationState(TernarySimulationState TSS){
    // std::cout << "SimulationState: " << TSS << " IFlag: " << TSS->IFlag << " IsIntersect: " << TSS->IsSat << 
    // " IsDone" << TSS->IsDone << std::endl;
    std::cout << "continuation" << e1.REnodeToString(TSS[0]->Ccontinuation) << std::endl;
    std::cout << "continuation" << e1.REnodeToString(TSS[1]->Ccontinuation) << std::endl;
    std::cout << "continuation" << e1.REnodeToString(TSS[2]->Ccontinuation) << std::endl;
    // F1.DumpState(TSS->NS1);
    // F1.DumpState(TSS->NS2->NS1);
    // F1.DumpState(TSS->NS2->NS2);
  }

  std::set<DetectABTNFA_Lookaround::TernarySimulationState> DetectABTNFA_Lookaround::DTSimulationState(TernarySimulationState TS){
    std::set<DetectABTNFA_Lookaround::TernarySimulationState> TSSSet;
    if (TS[0] == TS[1] && TS[0] != TS[2]){
      TSSSet.insert({TS[0], TS[2], TS[2]});
      TSSSet.insert({TS[2], TS[0], TS[1]});
    }
    else if (TS[1] == TS[2] && TS[0] != TS[1]){
      TSSSet.insert({TS[0], TS[0], TS[1]});
      TSSSet.insert({TS[0], TS[1], TS[0]});
    }
    return TSSSet;
  }

  bool DetectABTNFA_Lookaround::DetectABTOFS(TernarySimulationState TSS_Ex, std::set<TernarySimulationState> TSSET){
    if (debug.PrintSimulation){
      std::cout << "witness str: " << WitnessStr << std::endl;
      DumpTernarySimulationState(TSS_Ex);
    }
    std::queue<std::pair <TernarySimulationState, std::string>> Q;
    Q.push({TSS_Ex, ""});
    while (Q.size() > 0){
      std::pair <TernarySimulationState, std::string> TSS = Q.front();
      Q.pop();
      SimulationCache.insert(TSS.first);
      for (auto c : Alphabet){
        if (debug.PrintSimulation) std::cout << "matching: " << int(c) << " " << std::endl;
        WitnessStr = TSS.second;
        auto nextns1 = F1.StepOneByte(TSS.first[0], c);
        auto nextns2 = F1.StepOneByte(TSS.first[1], c);
        auto nextns3 = F1.StepOneByte(TSS.first[2], c);
        if (nextns1.empty() || nextns2.empty() || nextns3.empty())
          continue;
        for (auto nextns1_it : nextns1){
          // if (nextns1_it->DFlag == FollowAtomata::StateFlag::Match && e1.matchFlag != REnodeClass::MatchFlag::dollarEnd)
          //   continue;
          for (auto nextns2_it : nextns2){
            // if (nextns2_it->DFlag == FollowAtomata::StateFlag::Match  && e1.matchFlag != REnodeClass::MatchFlag::dollarEnd)
            //   continue;
            for (auto nextns3_it : nextns3){
              // if (nextns3_it->DFlag == FollowAtomata::StateFlag::Match && e1.matchFlag != REnodeClass::MatchFlag::dollarEnd)
              //   continue;
              TernarySimulationState ns ={nextns1_it, nextns2_it, nextns3_it};
              auto itc = SimulationCache.find(ns);
              if (itc != SimulationCache.end()){
                continue;
              }
              if (debug.PrintSimulation) DumpTernarySimulationState(ns);
              WitnessStr.push_back(c);
              Q.push(std::make_pair(ns, WitnessStr));
              if (TSSET.find(ns) != TSSET.end()){
                return true;
              }
              // if (DetectABTOFS(ns, TSSET)){
              //   return true;
              // }
              // else
              //   WitnessStr.pop_back();
            
            }
          }
        }
      }
    }
    return false;
  }

  bool DetectABTNFA_Lookaround::DetectABTOFSDeepFirst(TernarySimulationState TSS_Ex, std::set<TernarySimulationState> TSSET){
    if (debug.PrintSimulation){
      std::cout << "witness str: " << WitnessStr << std::endl;
      DumpTernarySimulationState(TSS_Ex);
    }
    // std::queue<std::pair <TernarySimulationState, std::string>> Q;
    // Q.push({TSS_Ex, ""});
    // while (Q.size() > 0){
    // std::pair <TernarySimulationState, std::string> TSS = Q.front();
    // Q.pop();
    // std::pair <TernarySimulationState, std::string> TSS = {TSS_Ex, ""};
    SimulationCache.insert(TSS_Ex);
    for (auto c : Alphabet){
      if (debug.PrintSimulation) std::cout << "matching: " << int(c) << " " << std::endl;
      auto nextns1 = F1.StepOneByte(TSS_Ex[0], c);
      auto nextns2 = F1.StepOneByte(TSS_Ex[1], c);
      auto nextns3 = F1.StepOneByte(TSS_Ex[2], c);
      if (nextns1.empty() || nextns2.empty() || nextns3.empty())
        continue;
      for (auto nextns1_it : nextns1){
        // if (nextns1_it->DFlag == FollowAtomata::StateFlag::Match && e1.matchFlag != REnodeClass::MatchFlag::dollarEnd)
        //   continue;
        for (auto nextns2_it : nextns2){
          // if (nextns2_it->DFlag == FollowAtomata::StateFlag::Match  && e1.matchFlag != REnodeClass::MatchFlag::dollarEnd)
          //   continue;
          for (auto nextns3_it : nextns3){
            // if (nextns3_it->DFlag == FollowAtomata::StateFlag::Match && e1.matchFlag != REnodeClass::MatchFlag::dollarEnd)
            //   continue;
            TernarySimulationState ns ={nextns1_it, nextns2_it, nextns3_it};
            auto itc = SimulationCache.find(ns);
            if (itc != SimulationCache.end()){
              continue;
            }
            if (debug.PrintSimulation) DumpTernarySimulationState(ns);
            WitnessStr.push_back(c);
            if (TSSET.find(ns) != TSSET.end()){
              return true;
            }
            if (DetectABTOFSDeepFirst(ns, TSSET)){
              return true;
            }
            else
              WitnessStr.pop_back();
          
          }
        }
      }
    }
    // }
    return false;
  }

  bool DetectABTNFA_Lookaround::IsABT(TernarySimulationState TSS){
    if (debug.PrintSimulation){
      std::cout << "witness str: " << WitnessStr << std::endl;
      DumpTernarySimulationState(TSS);
    }
    for (auto c : Alphabet){
      if (debug.PrintSimulation) std::cout << "matching: " << int(c) << " " << std::endl;
      auto nextns1 = F1.StepOneByte(TSS[0], c);
      auto nextns2 = F1.StepOneByte(TSS[1], c);
      auto nextns3 = F1.StepOneByte(TSS[2], c);
      if (nextns1.empty() || nextns2.empty() || nextns3.empty())
        continue;
      for (auto nextns1_it : nextns1){
        for (auto nextns2_it : nextns2){
          for (auto nextns3_it : nextns3){
            TernarySimulationState ns =  getSorted({nextns1_it, nextns2_it, nextns3_it});
            if (debug.PrintSimulation) DumpTernarySimulationState(ns);
            auto itc = DoneCache.find(ns);
            if (itc != DoneCache.end()){
              continue;
            }
            else{
              DoneCache.insert(ns);
              auto TSSET = DTSimulationState(ns);
              InterStr.push_back(c);
              if (!TSSET.empty()){
                if (DetectABTOFSDeepFirst(ns, TSSET)){
                  std::string Preff = InterStr + WitnessStr;
                  if (Writefile()){  
                    if (isLazy)
                      return true;
                    else{
                      SimulationCache.clear();
                      WitnessStr = "";
                    }
                  }
                }
                else {
                  SimulationCache.clear();
                  WitnessStr = "";
                }
              }
              if (IsABT(ns)){
                return true;
              }
              else {
                InterStr.pop_back();
              }
            }
          }
        }
      }
    }
    return false;
  }
  
}