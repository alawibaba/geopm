/*
 * Copyright (c) 2015, 2016, Intel Corporation
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in
 *       the documentation and/or other materials provided with the
 *       distribution.
 *
 *     * Neither the name of Intel Corporation nor the names of its
 *       contributors may be used to endorse or promote products derived
 *       from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY LOG OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <iostream>
#include <string>
#include <fstream>
#include <system_error>

#include "gtest/gtest.h"
#include "geopm_error.h"
#include "Exception.hpp"
#include "PlatformImp.hpp"

#define NUM_CPU 16
#define NUM_TILE 4
#define NUM_PACKAGE 2

#ifndef NAME_MAX
#define NAME_MAX 1024
#endif

static const std::map<std::string, std::pair<off_t, unsigned long> > &test_msr_map(void);
static const std::map<std::string, std::pair<off_t, unsigned long> > &test_msr_map2(void);

class TestPlatformImp : public geopm::PlatformImp
{
    public:
        TestPlatformImp();
        virtual ~TestPlatformImp();
        virtual bool model_supported(int platform_id);
        virtual std::string platform_name();
        virtual void msr_path(int cpu);
        virtual void msr_initialize(void);
        virtual void msr_reset(void);
        virtual int power_control_domain(void) const;
        virtual int frequency_control_domain(void) const;
        virtual int performance_counter_domain(void) const;
        virtual double read_signal(int device_type, int device_index, int signal_type);
        virtual void batch_read_signal(std::vector<struct geopm::geopm_signal_descriptor> &signal_desc, bool is_changed);
        virtual void write_control(int device_type, int device_index, int signal_type, double value);

    protected:
        FRIEND_TEST(PlatformImpTest, parse_topology);
};

TestPlatformImp::TestPlatformImp()
    : PlatformImp(2, 5, 8.0, &(test_msr_map()))
{
    m_num_logical_cpu = NUM_CPU;
    m_num_hw_cpu = NUM_CPU;
    m_num_tile = NUM_TILE;
    m_num_package = NUM_PACKAGE;
    m_num_cpu_per_core = 1;

    for(off_t i = 0; (int)i < m_num_hw_cpu; i++) {
        msr_open(i);
    }
    //for negative tests
    m_cpu_file_desc.push_back(675);
}

TestPlatformImp::~TestPlatformImp()
{
    for(off_t i = 0; (int)i < m_num_hw_cpu; i++) {
        msr_close(i);
        snprintf(m_msr_path, NAME_MAX, "/tmp/msrfile%d", (int)i);
        remove(m_msr_path);
    }
}

bool TestPlatformImp::model_supported(int platform_id)
{
    return (platform_id == 0x999);
}

std::string TestPlatformImp::platform_name()
{
    std::string name = "test_platform";
    return name;
}

void TestPlatformImp::msr_initialize(void)
{
    return;
}

void TestPlatformImp::msr_reset(void)
{
    return;
}

int TestPlatformImp::power_control_domain(void) const
{
    return geopm::GEOPM_DOMAIN_PACKAGE;
}

int TestPlatformImp::frequency_control_domain(void) const
{
    return geopm::GEOPM_DOMAIN_CPU;
}

int TestPlatformImp::performance_counter_domain(void) const
{
    return geopm::GEOPM_DOMAIN_CPU;
}

void TestPlatformImp::msr_path(int cpu)
{
    uint32_t lval = 0x0;
    uint32_t hval = 0xFFFFFFFF;
    int err;
    std::ofstream msrfile;

    err = snprintf(m_msr_path, NAME_MAX, "/tmp/msrfile%d", cpu);
    ASSERT_TRUE(err >= 0);

    msrfile.open(m_msr_path, std::ios::out|std::ios::binary);
    ASSERT_TRUE(msrfile.is_open());

    for(uint64_t i = 0; i < NUM_CPU; i++) {
        lval = i;
        msrfile.write((const char*)&hval, sizeof(hval));
        msrfile.write((const char*)&lval, sizeof(lval));
    }

    msrfile.flush();
    msrfile.close();
    ASSERT_FALSE(msrfile.is_open());

    return;
}

double TestPlatformImp::read_signal(int device_type, int device_index, int signal_type)
{
    return 1.0;
}

void TestPlatformImp::batch_read_signal(std::vector<struct geopm::geopm_signal_descriptor> &signal_desc, bool is_changed)
{

}

void TestPlatformImp::write_control(int device_type, int device_index, int signal_type, double value)
{

}

class TestPlatformImp2 : public geopm::PlatformImp
{
    public:
        TestPlatformImp2();
        virtual ~TestPlatformImp2()
        {
            ;
        }
        virtual bool model_supported(int platform_id)
        {
            return true;
        }
        virtual void parse_hw_topology(void)
        {
            return;
        }
        virtual void msr_path(int cpu);
        virtual void msr_initialize(void)
        {
            return;
        }
        virtual void msr_reset(void)
        {
            return;
        }
        virtual int power_control_domain(void) const
        {
            return geopm::GEOPM_DOMAIN_PACKAGE;
        }
        virtual int frequency_control_domain(void) const
        {
            return geopm::GEOPM_DOMAIN_CPU;
        }
        virtual int performance_counter_domain(void) const
        {
            return geopm::GEOPM_DOMAIN_CPU;
        }
        virtual double read_signal(int device_type, int device_index, int signal_type)
        {
            return 1.0;
        }
        virtual void batch_read_signal(std::vector<struct geopm::geopm_signal_descriptor> &signal_desc, bool is_changed)
        {

        }
        virtual void write_control(int device_type, int device_index, int signal_type, double value)
        {

        }
        virtual std::string platform_name();
        std::vector<std::string> m_msr_list;

    protected:
        FRIEND_TEST(PlatformImpTest, negative_msr_open);
};

TestPlatformImp2::TestPlatformImp2()
    : PlatformImp(2, 5, 8.0, &(test_msr_map2()))
{
    m_num_logical_cpu = NUM_CPU;
    m_num_hw_cpu = NUM_CPU;
    m_num_tile = NUM_TILE;
    m_num_package = NUM_PACKAGE;
    m_num_cpu_per_core = 1;

    std::vector<std::string> msr_list = {
        "PKG_POWER_LIMIT",
        "PP0_POWER_LIMIT",
        "DRAM_POWER_LIMIT",
        "PERF_FIXED_CTR_CTRL",
        "PERF_GLOBAL_CTRL",
        "PERF_GLOBAL_OVF_CTRL",
        "IA32_PERF_CTL"
    };

    m_msr_list = msr_list;
}

void TestPlatformImp2::msr_path(int cpu)
{
    uint32_t lval = 0x0;
    uint32_t hval = 0xDEADBEEF;
    int err;
    std::ofstream msrfile;

    err = snprintf(m_msr_path, NAME_MAX, "/tmp/msrfile%d", cpu);
    ASSERT_TRUE(err >= 0);

    msrfile.open(m_msr_path, std::ios::out|std::ios::binary);
    ASSERT_TRUE(msrfile.is_open());

    for (unsigned int i = 0; i < m_msr_list.size(); i++) {
        msrfile.seekp(i*64);
        lval = i;
        msrfile.write((const char*)&lval, sizeof(lval));
        msrfile.write((const char*)&hval, sizeof(hval));
    }

    msrfile.flush();
    msrfile.close();
    ASSERT_FALSE(msrfile.is_open());

    return;
}

std::string TestPlatformImp2::platform_name()
{
    std::string name = "test_platform2";
    return name;
}

static const std::map<std::string, std::pair<off_t, unsigned long> > &test_msr_map(void)
{
    static const std::map<std::string, std::pair<off_t, unsigned long> > msr_map({
        {"MSR_TEST_0", {0, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_1", {64, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_2", {128, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_3", {192, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_4", {256, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_5", {320, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_6", {384, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_7", {448, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_8", {512, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_9", {576, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_10", {640, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_11", {704, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_12", {768, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_13", {832, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_14", {896, 0x0FFFFFFFFFFFFFFF}},
        {"MSR_TEST_15", {960, 0x0FFFFFFFFFFFFFFF}}});
    return msr_map;
}

static const std::map<std::string, std::pair<off_t, unsigned long> > &test_msr_map2(void)
{
    static const std::map<std::string, std::pair<off_t, unsigned long> > msr_map({
        {"PKG_POWER_LIMIT",      {0,   0xDFFFFFFFFFFFFFFF}},
        {"PP0_POWER_LIMIT",      {64,  0xDFFFFFFFFFFFFFFF}},
        {"DRAM_POWER_LIMIT",     {128, 0xDFFFFFFFFFFFFFFF}},
        {"PERF_FIXED_CTR_CTRL",  {192, 0xDFFFFFFFFFFFFFFF}},
        {"PERF_GLOBAL_CTRL",     {256, 0xDFFFFFFFFFFFFFFF}},
        {"PERF_GLOBAL_OVF_CTRL", {320, 0xDFFFFFFFFFFFFFFF}},
        {"IA32_PERF_CTL",        {384, 0xDFFFFFFFFFFFFFFF}}});
    return msr_map;
}
////////////////////////////////////////////////////////////////////

class PlatformImpTest: public :: testing :: Test
{
    public:
        PlatformImpTest();
        ~PlatformImpTest();
    protected:
        TestPlatformImp *m_platform;
};

PlatformImpTest::PlatformImpTest()
{
    m_platform = new TestPlatformImp();
}

PlatformImpTest::~PlatformImpTest()
{
    delete m_platform;
}

class PlatformImpTest2: public :: testing :: Test
{
    public:
        PlatformImpTest2();
        ~PlatformImpTest2();
    protected:
        TestPlatformImp2 *m_platform2;
        virtual void TearDown();
};

PlatformImpTest2::PlatformImpTest2()
{
    m_platform2 = new TestPlatformImp2();
}

PlatformImpTest2::~PlatformImpTest2()
{
}

void PlatformImpTest2::TearDown()
{
    char msr_path[NAME_MAX];

    for(int i = 0; i < NUM_CPU; i++) {
        /// @todo call msr_close in the destructor for the PlatformImp
        snprintf(msr_path, NAME_MAX, "/tmp/msrfile%d", i);
        remove(msr_path);
    }
}

TEST_F(PlatformImpTest, platform_get_name)
{
    std::string pname = "test_platform";
    std::string ans;

    ans = m_platform->platform_name();
    ASSERT_FALSE(ans.empty());

    EXPECT_FALSE(ans.compare(pname));
}

TEST_F(PlatformImpTest, platform_get_package)
{
    int num = m_platform->num_package();

    EXPECT_TRUE(num == NUM_PACKAGE);
}

TEST_F(PlatformImpTest, platform_get_tile)
{
    int num = m_platform->num_tile();

    EXPECT_TRUE(num == NUM_TILE);
}

TEST_F(PlatformImpTest, platform_get_cpu)
{
    int num = m_platform->num_hw_cpu();

    EXPECT_TRUE(num == NUM_CPU);
}

TEST_F(PlatformImpTest, platform_get_hyperthreaded)
{
    EXPECT_TRUE(m_platform->num_logical_cpu() == NUM_CPU);
}

TEST_F(PlatformImpTest, cpu_msr_read_write)
{
    uint64_t value;

    for(uint64_t i = 0; i < NUM_CPU; i++) {
        std::string name = "MSR_TEST_";
        name.append(std::to_string(i));
        m_platform->msr_write(geopm::GEOPM_DOMAIN_CPU, i, name, i);
    }

    for(uint64_t i = 0; i < NUM_CPU; i++) {
        std::string name = "MSR_TEST_";
        name.append(std::to_string(i));
        value = m_platform->msr_read(geopm::GEOPM_DOMAIN_CPU, i, name);
        EXPECT_TRUE((value == i));
    }
}

TEST_F(PlatformImpTest, tile_msr_read_write)
{
    uint64_t value;

    for(uint64_t i = 0; i < NUM_TILE; i++) {
        std::string name = "MSR_TEST_";
        name.append(std::to_string(i));
        m_platform->msr_write(geopm::GEOPM_DOMAIN_TILE, i, name, i*3);
    }

    for(uint64_t i = 0; i < NUM_TILE; i++) {
        std::string name = "MSR_TEST_";
        name.append(std::to_string(i));
        value = m_platform->msr_read(geopm::GEOPM_DOMAIN_TILE, i, name);
        EXPECT_TRUE((value == (i*3)));
    }
}

TEST_F(PlatformImpTest, package_msr_read_write)
{
    uint64_t value;

    for(uint64_t i = 0; i < NUM_PACKAGE; i++) {
        std::string name = "MSR_TEST_";
        name.append(std::to_string(i));
        m_platform->msr_write(geopm::GEOPM_DOMAIN_PACKAGE, i, name, i*5);
    }

    for(uint64_t i = 0; i < NUM_PACKAGE; i++) {
        std::string name = "MSR_TEST_";
        name.append(std::to_string(i));
        value = m_platform->msr_read(geopm::GEOPM_DOMAIN_PACKAGE, i, name);
        EXPECT_TRUE((value == (i*5)));
    }
}

TEST_F(PlatformImpTest, msr_write_whitelist)
{
    size_t size;
    std::ifstream val;
    FILE *fd;
    char *val_buf;
    bool same = false;

    const char key_buf[] = {"# MSR      Write Mask         # Comment\n" \
                            "0x00000000 0x0000000000000000 # MSR_TEST_0\n" \
                            "0x00000040 0x0000000000000000 # MSR_TEST_1\n" \
                            "0x00000280 0x0000000000000000 # MSR_TEST_10\n" \
                            "0x000002c0 0x0000000000000000 # MSR_TEST_11\n" \
                            "0x00000300 0x0000000000000000 # MSR_TEST_12\n" \
                            "0x00000340 0x0000000000000000 # MSR_TEST_13\n" \
                            "0x00000380 0x0000000000000000 # MSR_TEST_14\n" \
                            "0x000003c0 0x0000000000000000 # MSR_TEST_15\n" \
                            "0x00000080 0x0000000000000000 # MSR_TEST_2\n" \
                            "0x000000c0 0x0000000000000000 # MSR_TEST_3\n" \
                            "0x00000100 0x0000000000000000 # MSR_TEST_4\n" \
                            "0x00000140 0x0000000000000000 # MSR_TEST_5\n" \
                            "0x00000180 0x0000000000000000 # MSR_TEST_6\n" \
                            "0x000001c0 0x0000000000000000 # MSR_TEST_7\n" \
                            "0x00000200 0x0000000000000000 # MSR_TEST_8\n" \
                            "0x00000240 0x0000000000000000 # MSR_TEST_9\0"
                           };

    fd = fopen("/tmp/whitelist", "w");
    m_platform->whitelist(fd);
    fclose(fd);

    val.open("/tmp/whitelist");

    size = strlen(key_buf);
    //Compare with size + 1 due to null character at end of file
    EXPECT_TRUE((size_t)(val.seekg(0, std::ifstream::end).tellg()) == (size + 1));
    val.seekg(0, std::ifstream::beg);

    val_buf = (char*)malloc(size);
    val.read(val_buf, size);
    val.close();

    same = (memcmp(val_buf, key_buf, size) == 0);

    free(val_buf);

    EXPECT_TRUE(same);

    remove("/tmp/whitelist");
}

TEST_F(PlatformImpTest, negative_read_no_desc)
{
    int thrown = 0;
    std::string name = "MSR_TEST_0";

    try {
        (void) m_platform->msr_read(geopm::GEOPM_DOMAIN_CPU, (NUM_CPU+2), name);
    }
    catch(geopm::Exception e) {
        thrown = e.err_value();
    }

    EXPECT_TRUE((thrown == GEOPM_ERROR_MSR_READ));
}

TEST_F(PlatformImpTest, negative_write_no_desc)
{
    uint64_t value = 0x5;
    int thrown = 0;
    std::string name = "MSR_TEST_0";

    try {
        m_platform->msr_write(geopm::GEOPM_DOMAIN_CPU, (NUM_CPU+2), name, value);
    }
    catch(geopm::Exception e) {
        thrown = e.err_value();
    }

    EXPECT_TRUE((thrown == GEOPM_ERROR_MSR_WRITE));
}

TEST_F(PlatformImpTest, negative_read_bad_desc)
{
    int thrown = 0;
    std::string name = "MSR_TEST_0";

    try {
        (void) m_platform->msr_read(geopm::GEOPM_DOMAIN_CPU, NUM_CPU, name);
    }
    catch(std::runtime_error e) {
        thrown = 1;
    }

    EXPECT_TRUE((thrown==1));
}

TEST_F(PlatformImpTest, negative_write_bad_desc)
{
    uint64_t value = 0x5;
    int thrown = 0;
    std::string name = "MSR_TEST_0";

    try {
        m_platform->msr_write(geopm::GEOPM_DOMAIN_CPU, NUM_CPU, name, value);
    }
    catch(std::runtime_error e) {
        thrown = 1;
    }

    EXPECT_TRUE((thrown==1));
}

TEST_F(PlatformImpTest, negative_msr_open)
{
    int thrown = 0;
    TestPlatformImp2 p;

    try {
        p.msr_open(5000);
    }
    catch(geopm::Exception e) {
        thrown = 1;
    }

    EXPECT_TRUE((thrown==1));
}

TEST_F(PlatformImpTest, negative_msr_write_bad_value)
{
    // The write mask specified in the constructor is 0 from bits 63:60 and 1 from bits 59:0.
    EXPECT_THROW(m_platform->msr_write(geopm::GEOPM_DOMAIN_CPU, 0, "MSR_TEST_0", 0xF000000000000000),
        geopm::Exception);
}

TEST_F(PlatformImpTest, parse_topology)
{
    int thrown = 0;

    try {
        m_platform->parse_hw_topology();
    }
    catch(std::system_error e) {
        thrown = 1;
    }

    EXPECT_TRUE((thrown==0));

    EXPECT_TRUE((m_platform->num_package() > 0));
    EXPECT_TRUE((m_platform->num_hw_cpu() > 0));
}

TEST_F(PlatformImpTest2, int_type_checks)
{
    const char *large_value_str = "0xDEADBEEFCAFED00D";
    uint64_t large_value = 0xDEADBEEFCAFED00D;
    unsigned long ul_result;

    // If this test ever fails, we need to look at converting all our "unsigned long" code to "unsigned long long".
    // Since uint64_t is defined as an "unsigned long long", if sizeof(long) is < 8 then we'll have problems.
    EXPECT_EQ(
        sizeof(unsigned long),
        sizeof(uint64_t)
    );

    ul_result = strtoul(large_value_str, NULL, 0);
    EXPECT_EQ(large_value, ul_result);

    ul_result = large_value;
    EXPECT_EQ(ul_result, large_value);
}

TEST_F(PlatformImpTest2, msr_write_restore_read)
{
    const char *path = "/tmp/.geopm_msr_save_test";
    uint64_t value = 0xDEADBEEFCAFED00D;
    uint64_t read_value;

    // Open the MSR fd's
    m_platform2->initialize();

    // Write big value.
    for(uint64_t i = 0; i < NUM_PACKAGE; i++) {
        for (std::string s : m_platform2->m_msr_list) {
            m_platform2->msr_write(geopm::GEOPM_DOMAIN_PACKAGE, i, s, value);
        }
    }

    // Read back big value, verify contents
    for(uint64_t i = 0; i < NUM_PACKAGE; i++) {
        for (std::string s : m_platform2->m_msr_list) {
            read_value = m_platform2->msr_read(geopm::GEOPM_DOMAIN_PACKAGE, i, s);
            EXPECT_TRUE((read_value == value));
        }
    }

    // Write save file
    m_platform2->save_msr_state(path);

    // Restore from save file
    m_platform2->restore_msr_state(path);

    // Verify restored contents
    for(uint64_t i = 0; i < NUM_PACKAGE; i++) {
        for (std::string s : m_platform2->m_msr_list) {
            read_value = m_platform2->msr_read(geopm::GEOPM_DOMAIN_PACKAGE, i, s);
            EXPECT_TRUE((read_value == value));
        }
    }

    delete m_platform2;
}

